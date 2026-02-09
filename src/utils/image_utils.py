"""
图像处理工具函数
提供图像读取、转换、预处理等功能
"""

import cv2
import numpy as np
from PIL import Image, ImageOps, ImageFilter
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any, Union
import logging
import io
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ImageInfo:
    """图像信息数据类"""
    path: Path
    width: int
    height: int
    channels: int
    format: str
    size_bytes: int
    checksum: Optional[str] = None
    exif_data: Optional[Dict[str, Any]] = None


class ImageLoader:
    """图像加载器"""
    
    @staticmethod
    def load_image(filepath: Union[str, Path], 
                   mode: str = "rgb") -> Optional[np.ndarray]:
        """
        加载图像
        
        Args:
            filepath: 图像文件路径
            mode: 颜色模式 ("rgb", "bgr", "gray")
            
        Returns:
            图像数组或None
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            logger.error(f"图像文件不存在: {filepath}")
            return None
        
        try:
            if mode == "rgb":
                # 使用PIL读取RGB图像
                img = Image.open(filepath)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                return np.array(img)
            elif mode == "bgr":
                # 使用OpenCV读取BGR图像
                img = cv2.imread(str(filepath))
                if img is not None:
                    return img
            elif mode == "gray":
                # 读取灰度图像
                img = cv2.imread(str(filepath), cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    return img
            else:
                logger.error(f"不支持的图像模式: {mode}")
                
        except Exception as e:
            logger.error(f"加载图像失败 {filepath}: {e}")
        
        return None
    
    @staticmethod
    def load_image_pil(filepath: Union[str, Path]) -> Optional[Image.Image]:
        """
        使用PIL加载图像
        
        Args:
            filepath: 图像文件路径
            
        Returns:
            PIL图像对象或None
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            logger.error(f"图像文件不存在: {filepath}")
            return None
        
        try:
            img = Image.open(filepath)
            # 确保图像已加载
            img.load()
            return img
        except Exception as e:
            logger.error(f"使用PIL加载图像失败 {filepath}: {e}")
            return None
    
    @staticmethod
    def get_image_info(filepath: Union[str, Path]) -> Optional[ImageInfo]:
        """
        获取图像信息
        
        Args:
            filepath: 图像文件路径
            
        Returns:
            图像信息或None
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            return None
        
        try:
            # 使用PIL获取基本信息
            with Image.open(filepath) as img:
                width, height = img.size
                mode = img.mode
                format = img.format
                
                # 获取EXIF数据
                exif_data = None
                if hasattr(img, '_getexif') and img._getexif():
                    exif_data = {
                        tag: value 
                        for tag, value in img._getexif().items() 
                        if tag is not None
                    }
            
            # 文件大小
            size_bytes = filepath.stat().st_size
            
            # 计算校验和
            import hashlib
            with open(filepath, 'rb') as f:
                checksum = hashlib.md5(f.read()).hexdigest()
            
            # 确定通道数
            if mode in ['L', 'P']:
                channels = 1
            elif mode == 'RGB':
                channels = 3
            elif mode == 'RGBA':
                channels = 4
            else:
                channels = 0
            
            return ImageInfo(
                path=filepath,
                width=width,
                height=height,
                channels=channels,
                format=format,
                size_bytes=size_bytes,
                checksum=checksum,
                exif_data=exif_data
            )
            
        except Exception as e:
            logger.error(f"获取图像信息失败 {filepath}: {e}")
            return None


class ImageProcessor:
    """图像处理器"""
    
    @staticmethod
    def resize_image(image: np.ndarray, 
                     max_size: int = 1600,
                     maintain_aspect: bool = True) -> np.ndarray:
        """
        调整图像大小
        
        Args:
            image: 输入图像
            max_size: 最大尺寸（宽或高的最大值）
            maintain_aspect: 是否保持宽高比
            
        Returns:
            调整后的图像
        """
        if image is None:
            return image
        
        h, w = image.shape[:2]
        
        # 如果图像已经小于等于最大尺寸，直接返回
        if max(h, w) <= max_size:
            return image
        
        if maintain_aspect:
            # 保持宽高比
            if h > w:
                new_h = max_size
                new_w = int(w * max_size / h)
            else:
                new_w = max_size
                new_h = int(h * max_size / w)
        else:
            # 不保持宽高比，直接缩放到指定尺寸
            new_h = new_w = max_size
        
        # 使用高质量插值
        interpolation = cv2.INTER_AREA if max(h, w) > max_size else cv2.INTER_LINEAR
        
        return cv2.resize(image, (new_w, new_h), interpolation=interpolation)
    
    @staticmethod
    def normalize_image(image: np.ndarray,
                        mean: List[float] = None,
                        std: List[float] = None) -> np.ndarray:
        """
        归一化图像
        
        Args:
            image: 输入图像 (H, W, C)
            mean: 均值，如果为None则使用图像自身均值
            std: 标准差，如果为None则使用图像自身标准差
            
        Returns:
            归一化后的图像
        """
        if image is None:
            return image
        
        # 确保是浮点数
        image_float = image.astype(np.float32)
        
        if mean is None or std is None:
            # 计算图像的均值和标准差
            if len(image.shape) == 3:
                mean = np.mean(image_float, axis=(0, 1))
                std = np.std(image_float, axis=(0, 1))
            else:
                mean = np.mean(image_float)
                std = np.std(image_float)
        
        # 避免除零
        std = np.where(std == 0, 1.0, std)
        
        # 归一化
        normalized = (image_float - mean) / std
        
        return normalized
    
    @staticmethod
    def enhance_image(image: np.ndarray,
                      contrast: float = 1.0,
                      brightness: float = 0.0,
                      saturation: float = 1.0) -> np.ndarray:
        """
        增强图像（对比度、亮度、饱和度）
        
        Args:
            image: 输入图像
            contrast: 对比度系数（>1增加，<1减少）
            brightness: 亮度调整值（正数增加，负数减少）
            saturation: 饱和度系数（>1增加，<1减少）
            
        Returns:
            增强后的图像
        """
        if image is None:
            return image
        
        enhanced = image.copy().astype(np.float32)
        
        # 调整对比度和亮度
        enhanced = contrast * enhanced + brightness
        
        # 调整饱和度（仅对彩色图像）
        if len(enhanced.shape) == 3 and enhanced.shape[2] >= 3:
            # 转换到HSV空间调整饱和度
            hsv = cv2.cvtColor(enhanced.astype(np.uint8), cv2.COLOR_BGR2HSV)
            hsv = hsv.astype(np.float32)
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * saturation, 0, 255)
            enhanced = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
        
        # 确保值在有效范围内
        enhanced = np.clip(enhanced, 0, 255).astype(np.uint8)
        
        return enhanced
    
    @staticmethod
    def detect_blur(image: np.ndarray,
                    threshold: float = 100.0) -> Tuple[bool, float]:
        """
        检测图像是否模糊
        
        Args:
            image: 输入图像
            threshold: 模糊阈值（拉普拉斯方差）
            
        Returns:
            (是否模糊, 模糊分数)
        """
        if image is None:
            return True, 0.0
        
        # 转换为灰度图像
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # 计算拉普拉斯方差
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        is_blurry = laplacian_var < threshold
        
        return is_blurry, float(laplacian_var)
    
    @staticmethod
    def extract_patches(image: np.ndarray,
                        patch_size: Tuple[int, int] = (224, 224),
                        stride: Tuple[int, int] = None,
                        padding: bool = True) -> List[np.ndarray]:
        """
        提取图像块
        
        Args:
            image: 输入图像
            patch_size: 块大小 (height, width)
            stride: 滑动步长，如果为None则等于patch_size
            padding: 是否填充边界
            
        Returns:
            图像块列表
        """
        if image is None:
            return []
        
        h, w = image.shape[:2]
        patch_h, patch_w = patch_size
        
        if stride is None:
            stride_h, stride_w = patch_h, patch_w
        else:
            stride_h, stride_w = stride
        
        patches = []
        
        # 如果需要填充
        if padding:
            # 计算需要填充的大小
            pad_h = (patch_h - h % stride_h) % patch_h
            pad_w = (patch_w - w % stride_w) % patch_w
            
            # 对称填充
            if len(image.shape) == 3:
                pad_width = ((0, pad_h), (0, pad_w), (0, 0))
            else:
                pad_width = ((0, pad_h), (0, pad_w))
            
            image = np.pad(image, pad_width, mode='reflect')
            h, w = image.shape[:2]
        
        # 提取块
        for y in range(0, h - patch_h + 1, stride_h):
            for x in range(0, w - patch_w + 1, stride_w):
                patch = image[y:y+patch_h, x:x+patch_w]
                patches.append(patch)
        
        return patches
    
    @staticmethod
    def blend_patches(patches: List[np.ndarray],
                      original_size: Tuple[int, int],
                      patch_size: Tuple[int, int],
                      stride: Tuple[int, int]) -> np.ndarray:
        """
        合并图像块
        
        Args:
            patches: 图像块列表
            original_size: 原始图像大小 (height, width)
            patch_size: 块大小 (height, width)
            stride: 滑动步长
            
        Returns:
            合并后的图像
        """
        if not patches:
            return None
        
        h, w = original_size
        patch_h, patch_w = patch_size
        stride_h, stride_w = stride
        
        # 创建权重矩阵和输出图像
        if len(patches[0].shape) == 3:
            output = np.zeros((h, w, patches[0].shape[2]), dtype=np.float32)
            weight = np.zeros((h, w, 1), dtype=np.float32)
        else:
            output = np.zeros((h, w), dtype=np.float32)
            weight = np.zeros((h, w), dtype=np.float32)
        
        patch_idx = 0
        
        for y in range(0, h - patch_h + 1, stride_h):
            for x in range(0, w - patch_w + 1, stride_w):
                patch = patches[patch_idx]
                
                # 创建权重（简单的线性衰减）
                y_coords, x_coords = np.meshgrid(
                    np.linspace(-1, 1, patch_h),
                    np.linspace(-1, 1, patch_w),
                    indexing='ij'
                )
                distance = np.sqrt(y_coords**2 + x_coords**2)
                patch_weight = 1.0 / (1.0 + distance)
                patch_weight = patch_weight / np.max(patch_weight)
                
                if len(patch.shape) == 3:
                    patch_weight = patch_weight[:, :, np.newaxis]
                
                # 累加
                output[y:y+patch_h, x:x+patch_w] += patch * patch_weight
                weight[y:y+patch_h, x:x+patch_w] += patch_weight
                
                patch_idx += 1
        
        # 避免除零
        weight = np.where(weight == 0, 1.0, weight)
        output = output / weight
        
        return output.astype(patches[0].dtype)


class ImageIO:
    """图像输入输出工具"""
    
    @staticmethod
    def save_image(image: np.ndarray,
                   filepath: Union[str, Path],
                   quality: int = 95,
                   **kwargs) -> bool:
        """
        保存图像
        
        Args:
            image: 图像数据
            filepath: 保存路径
            quality: 保存质量（0-100）
            **kwargs: 其他参数
            
        Returns:
            是否保存成功
        """
        if image is None:
            logger.error("无法保存空图像")
            return False
        
        filepath = Path(filepath)
        
        try:
            # 确保目录存在
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # 根据文件扩展名选择保存方法
            suffix = filepath.suffix.lower()
            
            if suffix in ['.jpg', '.jpeg']:
                # JPEG格式
                params = [cv2.IMWRITE_JPEG_QUALITY, quality]
                if len(image.shape) == 3 and image.shape[2] == 4:
                    # 如果有alpha通道，转换为RGB
                    image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
                success = cv2.imwrite(str(filepath), image, params)
                
            elif suffix == '.png':
                # PNG格式
                params = [cv2.IMWRITE_PNG_COMPRESSION, 9 - quality // 10]
                success = cv2.imwrite(str(filepath), image, params)
                
            else:
                # 其他格式
                success = cv2.imwrite(str(filepath), image)
            
            if success:
                logger.debug(f"图像保存成功: {filepath}")
                return True
            else:
                logger.error(f"图像保存失败: {filepath}")
                return False
                
        except Exception as e:
            logger.error(f"图像保存失败 {filepath}: {e}")
            return False
    
    @staticmethod
    def image_to_bytes(image: np.ndarray,
                       format: str = 'JPEG',
                       quality: int = 95) -> Optional[bytes]:
        """
        将图像转换为字节
        
        Args:
            image: 图像数据
            format: 格式 ('JPEG', 'PNG')
            quality: 质量（0-100）
            
        Returns:
            字节数据或None
        """
        if image is None:
            return None
        
        try:
            # 转换颜色空间
            if len(image.shape) == 3:
                if image.shape[2] == 4:
                    # BGRA to RGBA
                    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA)
                else:
                    # BGR to RGB
                    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                # 灰度图像
                image_rgb = image
            
            # 转换为PIL图像
            pil_image = Image.fromarray(image_rgb)
            
            # 保存到字节缓冲区
            buffer = io.BytesIO()
            
            if format.upper() == 'JPEG':
                # JPEG不支持透明度
                if pil_image.mode == 'RGBA':
                    pil_image = pil_image.convert('RGB')
                pil_image.save(buffer, format='JPEG', quality=quality, optimize=True)
            else:
                pil_image.save(buffer, format=format.upper())
            
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"图像转换字节失败: {e}")
            return None
    
    @staticmethod
    def bytes_to_image(data: bytes) -> Optional[np.ndarray]:
        """
        将字节转换为图像
        
        Args:
            data: 字节数据
            
        Returns:
            图像数据或None
        """
        if not data:
            return None
        
        try:
            # 从字节读取图像
            nparr = np.frombuffer(data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
            return image
        except Exception as e:
            logger.error(f"字节转换图像失败: {e}")
            return None