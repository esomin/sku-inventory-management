package com.inventory.sku.generator;

import com.inventory.sku.dto.SKURequest;
import com.pholser.junit.quickcheck.generator.GenerationStatus;
import com.pholser.junit.quickcheck.generator.Generator;
import com.pholser.junit.quickcheck.random.SourceOfRandomness;

import java.util.Arrays;
import java.util.List;

/**
 * Custom generator for SKURequest objects for property-based testing.
 */
public class SKURequestGenerator extends Generator<SKURequest> {

    private static final List<String> CATEGORIES = Arrays.asList(
            "전자제품", "식품", "의류", "가구", "도서", "스포츠용품");

    public SKURequestGenerator() {
        super(SKURequest.class);
    }

    @Override
    public SKURequest generate(SourceOfRandomness random, GenerationStatus status) {
        String skuCode = generateSKUCode(random);
        String productName = generateProductName(random);
        String category = CATEGORIES.get(random.nextInt(CATEGORIES.size()));
        Integer currentStock = random.nextInt(0, 1000);
        Integer safeStock = random.nextInt(0, 500);
        Double dailyConsumptionRate = random.nextDouble(0.0, 50.0);

        return new SKURequest(
                skuCode,
                productName,
                category,
                currentStock,
                safeStock,
                dailyConsumptionRate,
                null, // chipset
                null, // brand
                null, // modelName
                null, // vram
                null // isOc
        );
    }

    private String generateSKUCode(SourceOfRandomness random) {
        // Generate SKU code like "SKU-XXXXX" where X is alphanumeric
        StringBuilder sb = new StringBuilder("SKU-");
        for (int i = 0; i < 5; i++) {
            if (random.nextBoolean()) {
                sb.append((char) ('A' + random.nextInt(26)));
            } else {
                sb.append(random.nextInt(10));
            }
        }
        return sb.toString();
    }

    private String generateProductName(SourceOfRandomness random) {
        String[] prefixes = { "프리미엄", "스탠다드", "베이직", "프로", "울트라" };
        String[] products = { "노트북", "마우스", "키보드", "모니터", "헤드셋", "의자", "책상" };

        return prefixes[random.nextInt(prefixes.length)] + " " +
                products[random.nextInt(products.length)];
    }
}
