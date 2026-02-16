"""
Document Processor Module
=========================
Handles extraction from any document format:
- Native PDFs (text-based)
- Scanned PDFs
- Images (phone photos, scans)
- Mixed quality documents

Uses a multi-layered approach:
1. Preprocessing (deskew, denoise, enhance)
2. Vision LLM for complex documents
3. OCR fallback for simple cases
"""

import os
import io
import base64
import tempfile
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Union
from dataclasses import dataclass
from enum import Enum

import numpy as np
from PIL import Image
import cv2

# Conditional imports for PDF handling
try:
    from pdf2image import convert_from_path, convert_from_bytes
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

# Conditional import for Tesseract
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


class DocumentType(Enum):
    """Types of documents we can process"""
    NATIVE_PDF = "native_pdf"
    SCANNED_PDF = "scanned_pdf"
    IMAGE = "image"
    UNKNOWN = "unknown"


class ExtractionMethod(Enum):
    """How the text was extracted"""
    DIRECT_TEXT = "direct_text"
    VISION_LLM = "vision_llm"
    OCR = "ocr"
    HYBRID = "hybrid"


@dataclass
class ProcessedPage:
    """Represents a processed document page"""
    page_number: int
    original_image: Optional[Image.Image]
    processed_image: Optional[Image.Image]
    extracted_text: str
    confidence: float
    extraction_method: ExtractionMethod
    preprocessing_applied: List[str]


@dataclass
class ProcessedDocument:
    """Represents a fully processed document"""
    filename: str
    document_type: DocumentType
    total_pages: int
    pages: List[ProcessedPage]
    full_text: str
    average_confidence: float
    processing_notes: List[str]


class ImagePreprocessor:
    """
    Handles image preprocessing to improve extraction quality.
    Particularly important for:
    - Phone photos (skewed, shadows, variable lighting)
    - Old scans (noise, fading)
    - Fax quality documents
    """
    
    @staticmethod
    def preprocess(image: np.ndarray, aggressive: bool = False) -> Tuple[np.ndarray, List[str]]:
        """
        Apply preprocessing pipeline to improve document readability.
        
        Args:
            image: Input image as numpy array (BGR or grayscale)
            aggressive: If True, apply more aggressive enhancement
            
        Returns:
            Tuple of (processed_image, list_of_applied_operations)
        """
        operations_applied = []
        
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            operations_applied.append("grayscale_conversion")
        else:
            gray = image.copy()
        
        # 1. Noise reduction
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        operations_applied.append("noise_reduction")
        
        # 2. Contrast enhancement using CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        operations_applied.append("contrast_enhancement")
        
        # 3. Deskew detection and correction
        deskewed, angle = ImagePreprocessor._deskew(enhanced)
        if abs(angle) > 0.5:
            operations_applied.append(f"deskew_{angle:.1f}_degrees")
            enhanced = deskewed
        
        # 4. Binarization (adaptive thresholding)
        if aggressive:
            binary = cv2.adaptiveThreshold(
                enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            operations_applied.append("adaptive_binarization")
            return binary, operations_applied
        
        return enhanced, operations_applied
    
    @staticmethod
    def _deskew(image: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Detect and correct document skew.
        
        Returns:
            Tuple of (deskewed_image, angle_corrected)
        """
        # Edge detection
        edges = cv2.Canny(image, 50, 150, apertureSize=3)
        
        # Hough line detection
        lines = cv2.HoughLinesP(
            edges, 1, np.pi/180, threshold=100,
            minLineLength=100, maxLineGap=10
        )
        
        if lines is None:
            return image, 0.0
        
        # Calculate angles
        angles = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if x2 - x1 != 0:
                angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
                # Only consider near-horizontal lines
                if abs(angle) < 45:
                    angles.append(angle)
        
        if not angles:
            return image, 0.0
        
        # Median angle (robust to outliers)
        median_angle = np.median(angles)
        
        # Only correct if significant skew
        if abs(median_angle) < 0.5:
            return image, 0.0
        
        # Rotate image
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
        rotated = cv2.warpAffine(
            image, rotation_matrix, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )
        
        return rotated, median_angle
    
    @staticmethod
    def detect_document_quality(image: np.ndarray) -> Dict:
        """
        Assess document image quality.
        
        Returns:
            Dictionary with quality metrics
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Sharpness (Laplacian variance)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Contrast
        contrast = gray.std()
        
        # Brightness
        brightness = gray.mean()
        
        # Noise estimation
        noise = ImagePreprocessor._estimate_noise(gray)
        
        # Overall quality score (0-100)
        quality_score = min(100, max(0,
            (laplacian_var / 500) * 30 +  # Sharpness contribution
            (contrast / 80) * 30 +         # Contrast contribution
            (1 - abs(brightness - 128) / 128) * 20 +  # Brightness contribution
            (1 - noise / 50) * 20          # Noise contribution
        ))
        
        return {
            "sharpness": laplacian_var,
            "contrast": contrast,
            "brightness": brightness,
            "noise_level": noise,
            "quality_score": quality_score,
            "is_low_quality": quality_score < 40
        }
    
    @staticmethod
    def _estimate_noise(image: np.ndarray) -> float:
        """Estimate image noise level using Laplacian."""
        H, W = image.shape
        M = [[1, -2, 1],
             [-2, 4, -2],
             [1, -2, 1]]
        sigma = np.sum(np.sum(np.abs(cv2.filter2D(image, -1, np.array(M)))))
        sigma = sigma * np.sqrt(0.5 * np.pi) / (6 * (W - 2) * (H - 2))
        return sigma


class DocumentProcessor:
    """
    Main document processing class.
    Handles any document format and extracts text optimally.
    """
    
    def __init__(self, vision_extractor=None, use_ocr_fallback: bool = True):
        """
        Initialize the document processor.
        
        Args:
            vision_extractor: Optional VisionExtractor instance for Vision LLM extraction
            use_ocr_fallback: Whether to use Tesseract OCR as fallback
        """
        self.vision_extractor = vision_extractor
        self.use_ocr_fallback = use_ocr_fallback and TESSERACT_AVAILABLE
        self.preprocessor = ImagePreprocessor()
    
    def process(self, file_path: str = None, file_bytes: bytes = None, 
                filename: str = "document") -> ProcessedDocument:
        """
        Process a document from file path or bytes.
        
        Args:
            file_path: Path to the document file
            file_bytes: Raw bytes of the document
            filename: Name for reference
            
        Returns:
            ProcessedDocument with all extracted content
        """
        if file_path:
            filename = Path(file_path).name
            with open(file_path, 'rb') as f:
                file_bytes = f.read()
        
        if not file_bytes:
            raise ValueError("Either file_path or file_bytes must be provided")
        
        # Detect document type
        doc_type = self._detect_document_type(file_bytes, filename)
        
        # Convert to images
        images = self._to_images(file_bytes, filename, doc_type)
        
        # Process each page
        pages = []
        processing_notes = []
        
        for i, img in enumerate(images):
            page = self._process_page(img, i + 1)
            pages.append(page)
            
            if page.confidence < 0.5:
                processing_notes.append(f"Page {i+1}: Low confidence extraction ({page.confidence:.2f})")
        
        # Combine full text
        full_text = "\n\n---PAGE BREAK---\n\n".join([p.extracted_text for p in pages])
        
        # Calculate average confidence
        avg_confidence = sum(p.confidence for p in pages) / len(pages) if pages else 0
        
        return ProcessedDocument(
            filename=filename,
            document_type=doc_type,
            total_pages=len(pages),
            pages=pages,
            full_text=full_text,
            average_confidence=avg_confidence,
            processing_notes=processing_notes
        )
    
    def _detect_document_type(self, file_bytes: bytes, filename: str) -> DocumentType:
        """Detect the type of document."""
        filename_lower = filename.lower()
        
        # Check file extension
        if filename_lower.endswith('.pdf'):
            # Check if it's a native or scanned PDF
            # Simple heuristic: native PDFs usually have text operators
            if b'/Type /Page' in file_bytes and b'BT' in file_bytes and b'ET' in file_bytes:
                # Likely has text content
                return DocumentType.NATIVE_PDF
            return DocumentType.SCANNED_PDF
        
        elif filename_lower.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp')):
            return DocumentType.IMAGE
        
        return DocumentType.UNKNOWN
    
    def _to_images(self, file_bytes: bytes, filename: str, 
                   doc_type: DocumentType) -> List[Image.Image]:
        """Convert document to list of PIL Images."""
        
        if doc_type in [DocumentType.NATIVE_PDF, DocumentType.SCANNED_PDF]:
            if not PDF2IMAGE_AVAILABLE:
                raise ImportError("pdf2image is required for PDF processing. Install with: pip install pdf2image")
            
            # Convert PDF pages to images
            try:
                images = convert_from_bytes(file_bytes, dpi=200)
                return images
            except Exception as e:
                raise ValueError(f"Failed to convert PDF: {str(e)}")
        
        elif doc_type == DocumentType.IMAGE:
            # Load image directly
            img = Image.open(io.BytesIO(file_bytes))
            if img.mode != 'RGB':
                img = img.convert('RGB')
            return [img]
        
        else:
            # Try to open as image anyway
            try:
                img = Image.open(io.BytesIO(file_bytes))
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                return [img]
            except:
                raise ValueError(f"Unable to process document type: {doc_type}")
    
    def _process_page(self, image: Image.Image, page_number: int) -> ProcessedPage:
        """Process a single page/image."""
        
        # Convert to numpy array for preprocessing
        img_array = np.array(image)
        
        # Assess quality
        quality = self.preprocessor.detect_document_quality(img_array)
        
        # Apply preprocessing
        processed_array, operations = self.preprocessor.preprocess(
            img_array, 
            aggressive=quality['is_low_quality']
        )
        
        # Convert back to PIL
        processed_image = Image.fromarray(processed_array)
        
        # Extract text
        extracted_text = ""
        confidence = 0.0
        method = ExtractionMethod.OCR
        
        # Try Vision LLM first (best for complex documents)
        if self.vision_extractor:
            try:
                result = self.vision_extractor.extract(image)
                if result and result.get('text'):
                    extracted_text = result['text']
                    confidence = result.get('confidence', 0.8)
                    method = ExtractionMethod.VISION_LLM
            except Exception as e:
                print(f"Vision extraction failed: {e}")
        
        # Fallback to OCR if needed
        if not extracted_text and self.use_ocr_fallback:
            try:
                # Use processed image for OCR
                ocr_result = pytesseract.image_to_data(
                    processed_image, 
                    output_type=pytesseract.Output.DICT
                )
                
                # Extract text and calculate confidence
                texts = []
                confidences = []
                
                for i, text in enumerate(ocr_result['text']):
                    if text.strip():
                        texts.append(text)
                        conf = ocr_result['conf'][i]
                        if conf > 0:  # -1 means no confidence
                            confidences.append(conf / 100)
                
                extracted_text = ' '.join(texts)
                confidence = sum(confidences) / len(confidences) if confidences else 0.0
                method = ExtractionMethod.OCR
                
            except Exception as e:
                print(f"OCR extraction failed: {e}")
                extracted_text = "[Extraction failed]"
                confidence = 0.0
        
        return ProcessedPage(
            page_number=page_number,
            original_image=image,
            processed_image=processed_image,
            extracted_text=extracted_text,
            confidence=confidence,
            extraction_method=method,
            preprocessing_applied=operations
        )


class VisionExtractor:
    """
    Extracts text from images using Vision LLMs.
    Supports: Google Gemini Vision, Groq Llama Vision
    """
    
    def __init__(self, provider: str = "gemini", api_key: str = None):
        """
        Initialize the vision extractor.
        
        Args:
            provider: "gemini" or "groq"
            api_key: API key for the provider
        """
        self.provider = provider.lower()
        self.api_key = api_key
        
        if self.provider == "gemini":
            self._init_gemini()
        elif self.provider == "groq":
            self._init_groq()
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    def _init_gemini(self):
        """Initialize Google Gemini."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            # FIXED: Use gemini-2.0-flash instead of deprecated gemini-1.5-flash
            self.model = genai.GenerativeModel('gemini-2.0-flash')
        except ImportError:
            raise ImportError("google-generativeai is required. Install with: pip install google-generativeai")
    
    def _init_groq(self):
        """Initialize Groq."""
        try:
            from groq import Groq
            self.client = Groq(api_key=self.api_key)
        except ImportError:
            raise ImportError("groq is required. Install with: pip install groq")
    
    def extract(self, image: Image.Image) -> Dict:
        """
        Extract text from an image using Vision LLM.
        
        Args:
            image: PIL Image
            
        Returns:
            Dictionary with 'text' and 'confidence'
        """
        if self.provider == "gemini":
            return self._extract_gemini(image)
        elif self.provider == "groq":
            return self._extract_groq(image)
    
    def _extract_gemini(self, image: Image.Image) -> Dict:
        """Extract using Google Gemini Vision."""
        prompt = """You are a document OCR specialist. Extract ALL text from this document image.

Instructions:
1. Extract every word, number, and symbol visible
2. Preserve the document structure (paragraphs, lists, tables)
3. For tables, use | to separate columns
4. Include headers, footers, and any fine print
5. If text is unclear, make your best interpretation and mark with [unclear]
6. Do not add any commentary - only output the extracted text

Begin extraction:"""
        
        try:
            response = self.model.generate_content([prompt, image])
            text = response.text
            
            return {
                "text": text,
                "confidence": 0.85  # Gemini doesn't provide confidence scores
            }
        except Exception as e:
            print(f"Gemini extraction error: {e}")
            return {"text": "", "confidence": 0.0}
    
    def _extract_groq(self, image: Image.Image) -> Dict:
        """Extract using Groq Llama Vision."""
        # Convert image to base64
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        prompt = """You are a document OCR specialist. Extract ALL text from this document image.

Instructions:
1. Extract every word, number, and symbol visible
2. Preserve the document structure (paragraphs, lists, tables)
3. For tables, use | to separate columns
4. Include headers, footers, and any fine print
5. If text is unclear, make your best interpretation and mark with [unclear]
6. Do not add any commentary - only output the extracted text

Begin extraction:"""
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.2-90b-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{img_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=4096
            )
            
            text = response.choices[0].message.content
            
            return {
                "text": text,
                "confidence": 0.85
            }
        except Exception as e:
            print(f"Groq extraction error: {e}")
            return {"text": "", "confidence": 0.0}


def image_to_base64(image: Image.Image, format: str = "PNG") -> str:
    """Convert PIL Image to base64 string."""
    buffered = io.BytesIO()
    image.save(buffered, format=format)
    return base64.b64encode(buffered.getvalue()).decode()


def base64_to_image(base64_string: str) -> Image.Image:
    """Convert base64 string to PIL Image."""
    image_data = base64.b64decode(base64_string)
    return Image.open(io.BytesIO(image_data))
