package com.inventory.sku.service;

import com.inventory.sku.dto.RiskAlertResponse;
import com.inventory.sku.entity.RiskAlert;
import com.inventory.sku.entity.SKU;
import com.inventory.sku.exception.SKUNotFoundException;
import com.inventory.sku.repository.RiskAlertRepository;
import com.inventory.sku.repository.SKURepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class RiskAlertServiceImpl implements RiskAlertService {

    private final RiskAlertRepository riskAlertRepository;
    private final SKURepository skuRepository;

    @Override
    public Page<RiskAlertResponse> getRiskAlerts(Boolean acknowledged, Long skuId,
            LocalDateTime startDate, LocalDateTime endDate,
            Pageable pageable) {
        Page<RiskAlert> riskAlerts;

        if (skuId != null && acknowledged != null) {
            // SKU ID와 확인 여부로 필터링
            riskAlerts = riskAlertRepository.findBySkuIdAndAcknowledged(skuId, acknowledged, pageable);
        } else if (skuId != null) {
            // SKU ID로만 필터링
            riskAlerts = riskAlertRepository.findBySkuId(skuId, pageable);
        } else if (acknowledged != null) {
            // 확인 여부로만 필터링
            riskAlerts = riskAlertRepository.findByAcknowledged(acknowledged, pageable);
        } else if (startDate != null && endDate != null) {
            // 날짜 범위로 필터링
            riskAlerts = riskAlertRepository.findByDateRange(startDate, endDate, pageable);
        } else {
            // 필터 없이 전체 조회
            riskAlerts = riskAlertRepository.findAll(pageable);
        }

        return riskAlerts.map(this::convertToResponse);
    }

    @Override
    @Transactional
    public RiskAlertResponse acknowledgeAlert(Long id) {
        RiskAlert riskAlert = riskAlertRepository.findById(id)
                .orElseThrow(() -> new SKUNotFoundException("위험 알림을 찾을 수 없습니다: " + id));

        riskAlert.setAcknowledged(true);
        RiskAlert savedAlert = riskAlertRepository.save(riskAlert);

        return convertToResponse(savedAlert);
    }

    @Override
    public Long getUnacknowledgedCount() {
        return riskAlertRepository.countUnacknowledged();
    }

    private RiskAlertResponse convertToResponse(RiskAlert riskAlert) {
        SKU sku = skuRepository.findById(riskAlert.getSkuId()).orElse(null);
        String productName = sku != null ? sku.getProductName() : null;

        RiskAlertResponse response = new RiskAlertResponse();
        response.setId(riskAlert.getId());
        response.setSkuId(riskAlert.getSkuId());
        response.setProductName(productName);
        response.setRiskIndex(riskAlert.getRiskIndex());
        response.setAlertMessage(riskAlert.getAlertMessage());
        response.setCreatedAt(riskAlert.getCreatedAt());
        response.setAcknowledged(riskAlert.getAcknowledged());
        response.setThreshold(riskAlert.getThreshold());
        response.setContributingFactors(riskAlert.getContributingFactors());
        return response;
    }
}
