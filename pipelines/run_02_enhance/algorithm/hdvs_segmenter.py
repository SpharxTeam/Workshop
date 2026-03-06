# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# HDVS分割器：基于异构双分支投票监督的半监督分割增强[citation:10]

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Optional

class HDVSSegmenter(nn.Module):
    """
    异构双分支投票监督分割器
    通过两个异构网络分支的投票机制提升分割质量
    """
    
    def __init__(self, num_classes: int = 80, backbone: str = 'resnet50'):
        super().__init__()
        self.num_classes = num_classes
        
        # 分支A：基于ResNet的编码器-解码器
        self.branch_a_encoder = self._build_encoder(backbone)
        self.branch_a_decoder = self._build_decoder()
        
        # 分支B：基于不同初始化的异构网络
        self.branch_b_encoder = self._build_encoder(backbone, different_init=True)
        self.branch_b_decoder = self._build_decoder()
        
        # 特征通信模块：促进双分支特征交流[citation:10]
        self.feature_communication = FeatureCommunicationModule()
        
        # 投票融合模块
        self.voting_fusion = VotingFusionModule()
    
    def _build_encoder(self, backbone: str, different_init: bool = False):
        """构建编码器，支持异构初始化"""
        # 这里可以接入Ultralytics的YOLO骨干网络
        # 实际实现时调用YOLO的backbone
        pass
    
    def _build_decoder(self):
        """构建轻量级解码器"""
        return nn.Sequential(
            nn.Conv2d(2048, 512, 3, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True),
            nn.Conv2d(512, self.num_classes, 1)
        )
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        前向传播
        
        Returns:
            pred_a: 分支A预测
            pred_b: 分支B预测
            fused_pred: 投票融合后的预测
        """
        # 分支A前向
        feat_a = self.branch_a_encoder(x)
        pred_a = self.branch_a_decoder(feat_a)
        
        # 分支B前向
        feat_b = self.branch_b_encoder(x)
        pred_b = self.branch_b_decoder(feat_b)
        
        # 特征通信：双分支特征交换[citation:10]
        feat_a, feat_b = self.feature_communication(feat_a, feat_b)
        
        # 投票融合
        fused_pred = self.voting_fusion(pred_a, pred_b)
        
        return pred_a, pred_b, fused_pred


class FeatureCommunicationModule(nn.Module):
    """特征通信模块：促进双分支特征交流"""
    
    def __init__(self, channels: int = 2048):
        super().__init__()
        self.transform_a = nn.Conv2d(channels, channels, 1)
        self.transform_b = nn.Conv2d(channels, channels, 1)
        self.gate = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Conv2d(channels * 2, channels, 1),
            nn.Sigmoid()
        )
    
    def forward(self, feat_a: torch.Tensor, feat_b: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        # 特征变换
        trans_a = self.transform_a(feat_a)
        trans_b = self.transform_b(feat_b)
        
        # 门控融合
        combined = torch.cat([trans_a, trans_b], dim=1)
        gate = self.gate(combined)
        
        # 通信后的特征
        new_feat_a = feat_a + gate * trans_b
        new_feat_b = feat_b + gate * trans_a
        
        return new_feat_a, new_feat_b


class VotingFusionModule(nn.Module):
    """投票融合模块：基于置信度的动态投票[citation:5]"""
    
    def forward(self, pred_a: torch.Tensor, pred_b: torch.Tensor) -> torch.Tensor:
        # 计算每个分支的置信度（softmax后最大值）
        prob_a = F.softmax(pred_a, dim=1)
        prob_b = F.softmax(pred_b, dim=1)
        
        conf_a, _ = prob_a.max(dim=1, keepdim=True)
        conf_b, _ = prob_b.max(dim=1, keepdim=True)
        
        # 动态权重
        weight_a = conf_a / (conf_a + conf_b + 1e-8)
        weight_b = 1 - weight_a
        
        # 加权融合
        fused = weight_a * prob_a + weight_b * prob_b
        
        return fused