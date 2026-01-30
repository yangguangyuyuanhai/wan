# -*- coding: utf-8 -*-
"""
海康相机采集节点插件
从海康工业相机采集图像数据
"""

import sys
import os
import platform
import time
from ctypes import *
from typing import Dict, Any, List, Tuple

# 添加SDK路径
currentsystem = platform.system()
if currentsystem == 'Windows':
    sdk_path = os.path.join(os.getenv('MVCAM_COMMON_RUNENV', ''), "Samples", "Python", "MvImport")
    if sdk_path and os.path.exists(sdk_path):
        sys.path.append(sdk_path)

try:
    from MvCameraControl_class import *
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    print("警告: 海康SDK未找到，CameraSourceNode将无法使用")

from engine.node import INode, NodeMetadata, ExecutionContext, NodeResult, NodeState
from engine.port import Port, PortType, DataType
from core.data_types import ImageType
from logger_config import get_logger

logger = get_logger("CameraSourceNode")


class CameraSourceNode(INode):
    """
    海康相机采集节点
    作为数据源节点，持续采集图像并推送到下游
    """
    
    __plugin_metadata__ = {
        'type': 'camera_hik',
        'name': '海康相机采集',
        'version': '1.0.0',
        'author': 'System',
        'description': '从海康工业相机采集图像',
        'category': 'basic',
        'dependencies': ['MvCameraControl_class']  # 声明依赖
    }
    
    def __init__(self, node_id: str, config: Dict[str, Any]):
        super().__init__(node_id, config)
        
        self.cam = None
        self.device_list = None
        self.is_opened = False
        self.is_grabbing = False
        self.frame_count = 0
        
        # 配置参数
        self.device_index = config.get('device_index', 0)
        self.exposure_time = config.get('exposure_time', 10000)  # μs
        self.gain = config.get('gain', 0.0)  # dB
        self.frame_rate = config.get('frame_rate', 30.0)  # fps
        self.trigger_mode = config.get('trigger_mode', False)
        self.grab_timeout = config.get('grab_timeout', 1000)  # ms
        self.enable_packet_size_optimization = config.get('enable_packet_size_optimization', True)
    
    def get_metadata(self) -> NodeMetadata:
        return NodeMetadata(
            name=self.__plugin_metadata__['name'],
            version=self.__plugin_metadata__['version'],
            author=self.__plugin_metadata__['author'],
            description=self.__plugin_metadata__['description'],
            category=self.__plugin_metadata__['category']
        )
    
    def get_ports(self) -> Tuple[List[Port], List[Port]]:
        """
        定义端口
        相机节点无输入，只有图像输出
        """
        inputs = []  # 无输入端口
        outputs = [
            Port(
                name="image",
                port_type=PortType.OUTPUT,
                data_type=DataType.IMAGE,
                required=True,
                description="采集的图像数据"
            )
        ]
        return inputs, outputs
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置"""
        try:
            # 检查必需的配置项
            if 'device_index' in config:
                if not isinstance(config['device_index'], int) or config['device_index'] < 0:
                    logger.error("device_index 必须是非负整数")
                    return False
            
            if 'exposure_time' in config:
                if not isinstance(config['exposure_time'], (int, float)) or config['exposure_time'] <= 0:
                    logger.error("exposure_time 必须是正数")
                    return False
            
            if 'frame_rate' in config:
                if not isinstance(config['frame_rate'], (int, float)) or config['frame_rate'] <= 0:
                    logger.error("frame_rate 必须是正数")
                    return False
            
            return True
            
        except Exception as e:
            logger.exception(f"配置验证异常: {e}")
            return False
    
    async def initialize(self):
        """初始化节点（打开相机）"""
        try:
            if not SDK_AVAILABLE:
                logger.error("海康SDK不可用")
                return False
            
            # 初始化SDK
            ret = MvCamera.MV_CC_Initialize()
            if ret == 0:
                logger.info("SDK初始化成功")
                sdk_version = MvCamera.MV_CC_GetSDKVersion()
                logger.info(f"SDK版本: 0x{sdk_version:x}")
            else:
                logger.error(f"SDK初始化失败: 0x{ret:x}")
                return False
            
            # 枚举设备
            device_count = self._enumerate_devices()
            if device_count == 0:
                logger.error("未找到相机设备")
                return False
            
            # 打开设备
            if not self._open_device(self.device_index):
                logger.error("打开设备失败")
                return False
            
            # 开始采集
            if not self._start_grabbing():
                logger.error("开始采集失败")
                return False
            
            logger.info(f"相机节点 {self.node_id} 初始化成功")
            return True
            
        except Exception as e:
            logger.exception(f"初始化异常: {e}")
            return False
    
    def _enumerate_devices(self) -> int:
        """枚举设备"""
        try:
            self.device_list = MV_CC_DEVICE_INFO_LIST()
            tlayer_type = MV_GIGE_DEVICE | MV_USB_DEVICE
            
            ret = MvCamera.MV_CC_EnumDevices(tlayer_type, self.device_list)
            if ret != 0:
                logger.error(f"枚举设备失败: 0x{ret:x}")
                return 0
            
            logger.info(f"找到 {self.device_list.nDeviceNum} 个设备")
            
            # 打印设备信息
            for i in range(self.device_list.nDeviceNum):
                mvcc_dev_info = cast(
                    self.device_list.pDeviceInfo[i],
                    POINTER(MV_CC_DEVICE_INFO)
                ).contents
                
                self._print_device_info(mvcc_dev_info, i)
            
            return self.device_list.nDeviceNum
            
        except Exception as e:
            logger.exception(f"枚举设备异常: {e}")
            return 0
    
    def _print_device_info(self, dev_info, index):
        """打印设备信息"""
        if dev_info.nTLayerType == MV_GIGE_DEVICE:
            model = self._decode_char(dev_info.SpecialInfo.stGigEInfo.chModelName)
            nip1 = ((dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0xff000000) >> 24)
            nip2 = ((dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x00ff0000) >> 16)
            nip3 = ((dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x0000ff00) >> 8)
            nip4 = (dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x000000ff)
            logger.info(f"  [{index}] GigE: {model} (IP: {nip1}.{nip2}.{nip3}.{nip4})")
            
        elif dev_info.nTLayerType == MV_USB_DEVICE:
            model = self._decode_char(dev_info.SpecialInfo.stUsb3VInfo.chModelName)
            serial = self._decode_char(dev_info.SpecialInfo.stUsb3VInfo.chSerialNumber)
            logger.info(f"  [{index}] USB: {model} (SN: {serial})")
    
    def _decode_char(self, ctypes_char_array):
        """解码字符数组"""
        byte_str = memoryview(ctypes_char_array).tobytes()
        null_index = byte_str.find(b'\x00')
        if null_index != -1:
            byte_str = byte_str[:null_index]
        
        for encoding in ['gbk', 'utf-8', 'latin-1']:
            try:
                return byte_str.decode(encoding)
            except UnicodeDecodeError:
                continue
        return byte_str.decode('latin-1', errors='replace')
    
    def _open_device(self, device_index: int) -> bool:
        """打开设备"""
        try:
            if self.is_opened:
                logger.warning("设备已打开")
                return True
            
            # 创建相机对象
            self.cam = MvCamera()
            
            # 获取设备信息
            st_device_list = cast(
                self.device_list.pDeviceInfo[device_index],
                POINTER(MV_CC_DEVICE_INFO)
            ).contents
            
            # 创建句柄
            ret = self.cam.MV_CC_CreateHandle(st_device_list)
            if ret != 0:
                logger.error(f"创建句柄失败: 0x{ret:x}")
                return False
            
            # 打开设备
            ret = self.cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
            if ret != 0:
                logger.error(f"打开设备失败: 0x{ret:x}")
                return False
            
            logger.info("设备打开成功")
            self.is_opened = True
            
            # 优化网络参数（GigE相机）
            if st_device_list.nTLayerType == MV_GIGE_DEVICE:
                if self.enable_packet_size_optimization:
                    self._optimize_packet_size()
            
            # 设置相机参数
            self._set_camera_parameters()
            
            return True
            
        except Exception as e:
            logger.exception(f"打开设备异常: {e}")
            return False
    
    def _optimize_packet_size(self):
        """优化网络包大小"""
        try:
            packet_size = self.cam.MV_CC_GetOptimalPacketSize()
            if int(packet_size) > 0:
                ret = self.cam.MV_CC_SetIntValue("GevSCPSPacketSize", packet_size)
                if ret == 0:
                    logger.info(f"设置包大小: {packet_size} 字节")
                else:
                    logger.warning(f"设置包大小失败: 0x{ret:x}")
        except Exception as e:
            logger.exception(f"优化包大小异常: {e}")
    
    def _set_camera_parameters(self):
        """设置相机参数"""
        try:
            # 设置触发模式
            trigger_mode = MV_TRIGGER_MODE_ON if self.trigger_mode else MV_TRIGGER_MODE_OFF
            ret = self.cam.MV_CC_SetEnumValue("TriggerMode", trigger_mode)
            if ret == 0:
                mode_str = "触发" if self.trigger_mode else "连续"
                logger.info(f"设置触发模式: {mode_str}")
            
            # 设置曝光时间
            ret = self.cam.MV_CC_SetFloatValue("ExposureTime", self.exposure_time)
            if ret == 0:
                logger.info(f"设置曝光时间: {self.exposure_time} μs")
            
            # 设置增益
            ret = self.cam.MV_CC_SetFloatValue("Gain", self.gain)
            if ret == 0:
                logger.info(f"设置增益: {self.gain} dB")
            
            # 设置帧率
            ret = self.cam.MV_CC_SetFloatValue("AcquisitionFrameRate", self.frame_rate)
            if ret == 0:
                logger.info(f"设置帧率: {self.frame_rate} fps")
                
        except Exception as e:
            logger.exception(f"设置参数异常: {e}")
    
    def _start_grabbing(self) -> bool:
        """开始采集"""
        try:
            if not self.is_opened:
                logger.error("设备未打开")
                return False
            
            if self.is_grabbing:
                logger.warning("已在采集中")
                return True
            
            ret = self.cam.MV_CC_StartGrabbing()
            if ret != 0:
                logger.error(f"开始采集失败: 0x{ret:x}")
                return False
            
            logger.info("开始采集")
            self.is_grabbing = True
            return True
            
        except Exception as e:
            logger.exception(f"开始采集异常: {e}")
            return False
    
    async def run(self, context: ExecutionContext) -> NodeResult:
        """
        执行节点（采集图像）
        相机节点作为数据源，不需要输入数据
        
        注意：在流式执行器中，源节点会持续被调用
        """
        if not self.is_grabbing:
            return NodeResult(
                success=False,
                outputs={},
                error="相机未在采集状态"
            )
        
        try:
            # 获取图像
            st_out_frame = MV_FRAME_OUT()
            memset(byref(st_out_frame), 0, sizeof(st_out_frame))
            
            ret = self.cam.MV_CC_GetImageBuffer(st_out_frame, self.grab_timeout)
            
            if ret == 0 and st_out_frame.pBufAddr:
                self.frame_count += 1
                
                # 转换为numpy数组
                import numpy as np
                image_data = (c_ubyte * st_out_frame.stFrameInfo.nFrameLen)()
                memmove(byref(image_data), st_out_frame.pBufAddr, st_out_frame.stFrameInfo.nFrameLen)
                
                # 根据像素格式确定通道数
                pixel_format = st_out_frame.stFrameInfo.enPixelType
                width = st_out_frame.stFrameInfo.nWidth
                height = st_out_frame.stFrameInfo.nHeight
                
                # 简单处理：假设是单通道或三通道
                try:
                    if pixel_format in [PixelType_Gvsp_Mono8, PixelType_Gvsp_Mono10, PixelType_Gvsp_Mono12]:
                        # 单通道灰度图
                        image_array = np.frombuffer(image_data, dtype=np.uint8).reshape(height, width)
                    else:
                        # 三通道彩色图（BGR）
                        image_array = np.frombuffer(image_data, dtype=np.uint8).reshape(height, width, 3)
                except:
                    # 如果reshape失败，尝试自动推断
                    total_bytes = len(image_data)
                    if total_bytes == width * height:
                        image_array = np.frombuffer(image_data, dtype=np.uint8).reshape(height, width)
                    elif total_bytes == width * height * 3:
                        image_array = np.frombuffer(image_data, dtype=np.uint8).reshape(height, width, 3)
                    else:
                        raise ValueError(f"无法推断图像格式: {total_bytes} bytes for {width}x{height}")
                
                # 创建ImageType数据
                image = ImageType(
                    data=image_array,
                    width=width,
                    height=height,
                    format="BGR" if len(image_array.shape) == 3 else "GRAY",
                    metadata={
                        'frame_number': self.frame_count,
                        'timestamp': time.time(),
                        'pixel_format': pixel_format
                    }
                )
                
                # 释放缓冲区
                self.cam.MV_CC_FreeImageBuffer(st_out_frame)
                
                # 记录日志（每100帧）
                if self.frame_count % 100 == 0:
                    logger.info(f"已采集 {self.frame_count} 帧")
                
                return NodeResult(
                    success=True,
                    outputs={'image': image},
                    metadata={'frame_count': self.frame_count}
                )
            else:
                if ret != 0:
                    logger.debug(f"获取图像失败: 0x{ret:x}")
                return NodeResult(
                    success=False,
                    outputs={},
                    error=f"获取图像失败: 0x{ret:x}"
                )
                
        except Exception as e:
            logger.exception(f"采集图像异常: {e}")
            return NodeResult(
                success=False,
                outputs={},
                error=str(e)
            )
    
    async def cleanup(self):
        """清理资源（关闭相机）"""
        try:
            # 停止采集
            if self.is_grabbing:
                ret = self.cam.MV_CC_StopGrabbing()
                if ret == 0:
                    logger.info("停止采集")
                    self.is_grabbing = False
            
            # 关闭设备
            if self.is_opened and self.cam:
                ret = self.cam.MV_CC_CloseDevice()
                if ret == 0:
                    logger.info("设备已关闭")
                
                self.cam.MV_CC_DestroyHandle()
                self.is_opened = False
            
            # 清理SDK
            try:
                MvCamera.MV_CC_Finalize()
            except:
                pass
            
            logger.info(f"相机节点 {self.node_id} 清理完成")
            
        except Exception as e:
            logger.exception(f"清理资源异常: {e}")
