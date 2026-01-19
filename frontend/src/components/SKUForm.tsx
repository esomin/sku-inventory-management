import { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { skuApi } from '@/api/skuApi';
import type { SKURequest, SKUResponse } from '@/types/sku';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogFooter,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { NativeSelect, NativeSelectOption } from '@/components/ui/native-select';

interface SKUFormProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    sku?: SKUResponse | null;
}

/**
 * SKUForm component for creating and editing SKUs
 * Validates: Requirements 1.1, 1.2, 3.1
 */
export function SKUForm({ open, onOpenChange, sku }: SKUFormProps) {
    const queryClient = useQueryClient();
    const isEditMode = !!sku;

    const [formData, setFormData] = useState<SKURequest>({
        skuCode: '',
        productName: '',
        category: '',
        currentStock: 0,
        safeStock: 0,
        dailyConsumptionRate: 0,
    });

    const [errors, setErrors] = useState<Partial<Record<keyof SKURequest, string>>>({});

    // Reset form when dialog opens/closes or sku changes
    useEffect(() => {
        if (open) {
            if (sku) {
                setFormData({
                    skuCode: sku.skuCode,
                    productName: sku.productName,
                    category: sku.category,
                    currentStock: sku.currentStock,
                    safeStock: sku.safeStock,
                    dailyConsumptionRate: 0, // Not in response, use default
                });
            } else {
                setFormData({
                    skuCode: '',
                    productName: '',
                    category: '',
                    currentStock: 0,
                    safeStock: 0,
                    dailyConsumptionRate: 0,
                });
            }
            setErrors({});
        }
    }, [open, sku]);

    const createMutation = useMutation({
        mutationFn: (data: SKURequest) => skuApi.create(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['skus'] });
            toast.success('SKU가 성공적으로 생성되었습니다');
            onOpenChange(false);
        },
    });

    const updateMutation = useMutation({
        mutationFn: (data: SKURequest) => skuApi.update(sku!.id, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['skus'] });
            toast.success('SKU가 성공적으로 수정되었습니다');
            onOpenChange(false);
        },
    });

    const validateForm = (): boolean => {
        const newErrors: Partial<Record<keyof SKURequest, string>> = {};

        // Required field validation (Requirement 1.2)
        if (!formData.skuCode.trim()) {
            newErrors.skuCode = 'SKU 코드는 필수입니다';
        }
        if (!formData.productName.trim()) {
            newErrors.productName = '제품명은 필수입니다';
        }
        if (!formData.category.trim()) {
            newErrors.category = '카테고리는 필수입니다';
        }

        // Numeric validation
        if (formData.currentStock < 0) {
            newErrors.currentStock = '현재 재고는 0 이상이어야 합니다';
        }
        if (formData.safeStock < 0) {
            newErrors.safeStock = '안전 재고는 0 이상이어야 합니다';
        }
        if (formData.dailyConsumptionRate < 0) {
            newErrors.dailyConsumptionRate = '일일 소비량은 0 이상이어야 합니다';
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();

        if (!validateForm()) {
            toast.error('입력값을 확인해주세요');
            return;
        }

        if (isEditMode) {
            updateMutation.mutate(formData);
        } else {
            createMutation.mutate(formData);
        }
    };

    const handleChange = (field: keyof SKURequest, value: string | number) => {
        setFormData(prev => ({ ...prev, [field]: value }));
        // Clear error for this field when user starts typing
        if (errors[field]) {
            setErrors(prev => ({ ...prev, [field]: undefined }));
        }
    };

    const isPending = createMutation.isPending || updateMutation.isPending;

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                    <DialogTitle>
                        {isEditMode ? 'SKU 수정' : 'SKU 생성'}
                    </DialogTitle>
                </DialogHeader>

                <form onSubmit={handleSubmit}>
                    <div className="grid gap-4 py-4">
                        {/* SKU Code */}
                        <div className="grid gap-2">
                            <Label htmlFor="skuCode">
                                SKU 코드 <span className="text-red-500">*</span>
                            </Label>
                            <Input
                                id="skuCode"
                                value={formData.skuCode}
                                onChange={(e) => handleChange('skuCode', e.target.value)}
                                placeholder="예: SKU001"
                                disabled={isPending}
                            />
                            {errors.skuCode && (
                                <p className="text-sm text-red-500">{errors.skuCode}</p>
                            )}
                        </div>

                        {/* Product Name */}
                        <div className="grid gap-2">
                            <Label htmlFor="productName">
                                제품명 <span className="text-red-500">*</span>
                            </Label>
                            <Input
                                id="productName"
                                value={formData.productName}
                                onChange={(e) => handleChange('productName', e.target.value)}
                                placeholder="예: 노트북"
                                disabled={isPending}
                            />
                            {errors.productName && (
                                <p className="text-sm text-red-500">{errors.productName}</p>
                            )}
                        </div>

                        {/* Category */}
                        <div className="grid gap-2">
                            <Label htmlFor="category">
                                카테고리 <span className="text-red-500">*</span>
                            </Label>
                            <NativeSelect
                                id="category"
                                value={formData.category}
                                onChange={(e) => handleChange('category', e.target.value)}
                                disabled={isPending}
                            >
                                <NativeSelectOption value="">선택하세요</NativeSelectOption>
                                <NativeSelectOption value="전자제품">전자제품</NativeSelectOption>
                                <NativeSelectOption value="식품">식품</NativeSelectOption>
                                <NativeSelectOption value="의류">의류</NativeSelectOption>
                            </NativeSelect>
                            {errors.category && (
                                <p className="text-sm text-red-500">{errors.category}</p>
                            )}
                        </div>

                        {/* Current Stock */}
                        <div className="grid gap-2">
                            <Label htmlFor="currentStock">
                                현재 재고 <span className="text-red-500">*</span>
                            </Label>
                            <Input
                                id="currentStock"
                                type="number"
                                min="0"
                                value={formData.currentStock}
                                onChange={(e) => handleChange('currentStock', parseInt(e.target.value) || 0)}
                                disabled={isPending}
                            />
                            {errors.currentStock && (
                                <p className="text-sm text-red-500">{errors.currentStock}</p>
                            )}
                        </div>

                        {/* Safe Stock */}
                        <div className="grid gap-2">
                            <Label htmlFor="safeStock">
                                안전 재고 <span className="text-red-500">*</span>
                            </Label>
                            <Input
                                id="safeStock"
                                type="number"
                                min="0"
                                value={formData.safeStock}
                                onChange={(e) => handleChange('safeStock', parseInt(e.target.value) || 0)}
                                disabled={isPending}
                            />
                            {errors.safeStock && (
                                <p className="text-sm text-red-500">{errors.safeStock}</p>
                            )}
                        </div>

                        {/* Daily Consumption Rate */}
                        <div className="grid gap-2">
                            <Label htmlFor="dailyConsumptionRate">
                                일일 소비량 <span className="text-red-500">*</span>
                            </Label>
                            <Input
                                id="dailyConsumptionRate"
                                type="number"
                                min="0"
                                step="0.1"
                                value={formData.dailyConsumptionRate}
                                onChange={(e) => handleChange('dailyConsumptionRate', parseFloat(e.target.value) || 0)}
                                disabled={isPending}
                            />
                            {errors.dailyConsumptionRate && (
                                <p className="text-sm text-red-500">{errors.dailyConsumptionRate}</p>
                            )}
                        </div>
                    </div>

                    <DialogFooter>
                        <Button
                            type="button"
                            variant="outline"
                            onClick={() => onOpenChange(false)}
                            disabled={isPending}
                        >
                            취소
                        </Button>
                        <Button type="submit" disabled={isPending}>
                            {isPending ? '처리 중...' : isEditMode ? '수정' : '생성'}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}
