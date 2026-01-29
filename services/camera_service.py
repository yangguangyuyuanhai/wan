# -*- coding: utf-8 -*-
"""
相机采集服务
负责从工业相机采集图像数据
"""

import sys
import os
import platform
import threading
import time
from ctypes import *

# 添加SDK路径
currentsystem = platform.system()
if currentsystem == 'Windows':
    sys.path.append(os.path.join(os.getenv('MVCAM_COMMON_RUNENV'), "Samples", "Python", "MvImport"))
else:
    sys.path.append(os.path.join("Development", "Samples", "Python", "MvImport"))

from MvCameraControl_class import *
from pipeline_core import Filter, DataPacket
from logger_config import get_logger

logger = get_logger("CameraService")


class CameraService(Filter):
    """
    相机采集服务
    作为管道的数据源，持续采集图像
    """
    
    def __init__(self, config):
        """
        初始化相机服务
        
        Args:
            config: CameraServiceConfig配置对象
        """
        super().__init__("CameraService", config)
        
        self.cam = None
        self.device_list = None
        self.is_opened = False
        self.is_grabbing = False
        self.frame_count = 0
        
        # 初始化SDK
        self._initialize_sdk()
    
    def _initialize_sdk(self):
        """初始化SDK"""
        try:
            ret = MvCamera.MV_CC_Initialize()
            if ret == 0:
                logger.info("SDK初始化成功")
                sdk_version = MvCamera.MV_CC_GetSDKVersion()
                logger.info(f"SDK版本: 0x{sdk_version:x}")
            else:
                logger.error(f"SDK初始化失败: 0x{ret:x}")
        except Exception as e:
            logger.exception(f"SDK初始化异常: {e}")
    
    def enumerate_devices(self):
        """
        枚举设备
        
        Returns:
            设备数量
        """
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
    
    def open_device(self, device_index=0):
        """
        打开设备
        
        Args:
            device_index: 设备索引
            
        Returns:
            是否成功
        """
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
                if self.config.enable_packet_size_optimization:
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
            trigger_mode = MV_TRIGGER_MODE_ON if self.config.trigger_mode else MV_TRIGGER_MODE_OFF
            ret = self.cam.MV_CC_SetEnumValue("TriggerMode", trigger_mode)
            if ret == 0:
                mode_str = "触发" if self.config.trigger_mode else "连续"
                logger.info(f"设置触发模式: {mode_str}")
            
            # 设置曝光时间
            ret = self.cam.MV_CC_SetFloatValue("ExposureTime", self.config.exposure_time)
            if ret == 0:
                logger.info(f"设置曝光时间: {self.config.exposure_time} μs")
            
            # 设置增益
            ret = self.cam.MV_CC_SetFloatValue("Gain", self.config.gain)
            if ret == 0:
                logger.info(f"设置增益: {self.config.gain} dB")
            
            # 设置帧率
            ret = self.cam.MV_CC_SetFloatValue("AcquisitionFrameRate", self.config.frame_rate)
            if ret == 0:
                logger.info(f"设置帧率: {self.config.frame_rate} fps")
                
        except Exception as e:
            logger.exception(f"设置参数异常: {e}")
    
    def start_grabbing(self):
        """
        开始采集
        
        Returns:
            是否成功
        """
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
    
    def stop_grabbing(self):
        """停止采集"""
        try:
            if self.is_grabbing:
                ret = self.cam.MV_CC_StopGrabbing()
                if ret == 0:
                    logger.info("停止采集")
                    self.is_grabbing = False
        except Exception as e:
            logger.exception(f"停止采集异常: {e}")
    
    def close_device(self):
        """关闭设备"""
        try:
            self.stop_grabbing()
            
            if self.is_opened and self.cam:
                ret = self.cam.MV_CC_CloseDevice()
                if ret == 0:
                    logger.info("设备已关闭")
                
                self.cam.MV_CC_DestroyHandle()
                self.is_opened = False
                
        except Exception as e:
            logger.exception(f"关闭设备异常: {e}")
    
    def process(self, packet: DataPacket) -> DataPacket:
        """
        处理方法（采集图像）
        注意：相机服务作为数据源，不接收输入packet
        
        Args:
            packet: 输入数据包（忽略）
            
        Returns:
            包含图像的数据包
        """
        if not self.is_grabbing:
            return None
        
        try:
            # 获取图像
            st_out_frame = MV_FRAME_OUT()
            memset(byref(st_out_frame), 0, sizeof(st_out_frame))
            
            ret = self.cam.MV_CC_GetImageBuffer(st_out_frame, self.config.grab_timeout)
            
            if ret == 0 and st_out_frame.pBufAddr:
                self.frame_count += 1
                
                # 创建数据包
                packet = DataPacket(
                    packet_id=self.frame_count,
                    timestamp=time.time(),
                    image=st_out_frame.pBufAddr,
                    width=st_out_frame.stFrameInfo.nWidth,
                    height=st_out_frame.stFrameInfo.nHeight,
                    pixel_format=st_out_frame.stFrameInfo.enPixelType,
                    frame_number=self.frame_count
                )
                
                # 记录日志（每100帧）
                if self.frame_count % 100 == 0:
                    logger.info(f"已采集 {self.frame_count} 帧")
                
                # 释放缓冲区
                self.cam.MV_CC_FreeImageBuffer(st_out_frame)
                
                return packet
            else:
                if ret != 0:
                    logger.debug(f"获取图像失败: 0x{ret:x}")
                return None
                
        except Exception as e:
            logger.exception(f"采集图像异常: {e}")
            return None
    
    def __del__(self):
        """析构函数"""
        self.close_device()
        try:
            MvCamera.MV_CC_Finalize()
        except:
            pass
