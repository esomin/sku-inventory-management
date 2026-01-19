import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { skuApi } from '@/api/skuApi';
import type { SKUResponse } from '@/types/sku';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { ArrowUpDown, Pencil, Trash2 } from 'lucide-react';

interface SKUTableProps {
    searchTerm: string;
    category: string;
    problemStockOnly: boolean;
    onEdit: (sku: SKUResponse) => void;
}

export function SKUTable({ searchTerm, category, problemStockOnly, onEdit }: SKUTableProps) {
    const [sortBy, setSortBy] = useState('id');
    const [sortDirection, setSortDirection] = useState<'ASC' | 'DESC'>('ASC');
    const [page, setPage] = useState(0);
    const queryClient = useQueryClient();

    const { data, isLoading, error } = useQuery({
        queryKey: ['skus', searchTerm, category, problemStockOnly, page, sortBy, sortDirection],
        queryFn: () => skuApi.getAll({
            searchTerm: searchTerm || undefined,
            category: category || undefined,
            problemStockOnly,
            page,
            size: 10,
            sortBy,
            sortDirection,
        }).then(res => res.data),
    });

    const deleteMutation = useMutation({
        mutationFn: (id: number) => skuApi.delete(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['skus'] });
            toast.success('SKU가 성공적으로 삭제되었습니다');
        },
    });

    const handleSort = (column: string) => {
        if (sortBy === column) {
            setSortDirection(sortDirection === 'ASC' ? 'DESC' : 'ASC');
        } else {
            setSortBy(column);
            setSortDirection('ASC');
        }
    };

    const handleDelete = (id: number) => {
        if (window.confirm('정말로 이 SKU를 삭제하시겠습니까?')) {
            deleteMutation.mutate(id);
        }
    };

    const getRiskLevelColor = (riskLevel: string) => {
        switch (riskLevel) {
            case '높음': return 'text-red-600 font-semibold';
            case '중간': return 'text-yellow-600 font-semibold';
            case '낮음': return 'text-green-600';
            default: return '';
        }
    };

    if (isLoading) {
        return (
            <div className="flex justify-center items-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="text-center py-8 text-red-600">
                오류가 발생했습니다: {error instanceof Error ? error.message : '알 수 없는 오류'}
            </div>
        );
    }

    if (!data || data.content.length === 0) {
        return (
            <div className="text-center py-8 text-gray-500">
                No data
            </div>
        );
    }

    return (
        <div>
            <Table>
                <TableHeader>
                    <TableRow>
                        <TableHead>SKU 코드</TableHead>
                        <TableHead>
                            <Button variant="ghost" onClick={() => handleSort('productName')} className="p-0 h-auto font-medium">
                                제품명 <ArrowUpDown className="ml-2 h-4 w-4" />
                            </Button>
                        </TableHead>
                        <TableHead>카테고리</TableHead>
                        <TableHead className="text-right">현재 재고</TableHead>
                        <TableHead className="text-right">안전 재고</TableHead>
                        <TableHead>품절 위험</TableHead>
                        <TableHead>
                            <Button variant="ghost" onClick={() => handleSort('expectedShortageDate')} className="p-0 h-auto font-medium">
                                예상 품절일 <ArrowUpDown className="ml-2 h-4 w-4" />
                            </Button>
                        </TableHead>
                        <TableHead className="text-right">작업</TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {data.content.map((sku: SKUResponse) => (
                        <TableRow key={sku.id}>
                            <TableCell className="font-medium">{sku.skuCode}</TableCell>
                            <TableCell>{sku.productName}</TableCell>
                            <TableCell>{sku.category}</TableCell>
                            <TableCell className="text-right">{sku.currentStock}</TableCell>
                            <TableCell className="text-right">{sku.safeStock}</TableCell>
                            <TableCell className={getRiskLevelColor(sku.riskLevel)}>
                                {sku.riskLevel}
                            </TableCell>
                            <TableCell>
                                {sku.expectedShortageDate || '-'}
                            </TableCell>
                            <TableCell className="text-right">
                                <div className="flex justify-end gap-2">
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() => onEdit(sku)}
                                    >
                                        <Pencil className="h-4 w-4" />
                                    </Button>
                                    <Button
                                        variant="destructive"
                                        size="sm"
                                        onClick={() => handleDelete(sku.id)}
                                        disabled={deleteMutation.isPending}
                                    >
                                        <Trash2 className="h-4 w-4" />
                                    </Button>
                                </div>
                            </TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>

            {/* Pagination */}
            <div className="flex justify-between items-center mt-4">
                <Button
                    onClick={() => setPage(p => Math.max(0, p - 1))}
                    disabled={page === 0}
                    variant="outline"
                >
                    이전
                </Button>
                <span className="text-sm text-gray-600">
                    페이지 {page + 1} / {data.totalPages || 1}
                </span>
                <Button
                    onClick={() => setPage(p => p + 1)}
                    disabled={page >= (data.totalPages - 1)}
                    variant="outline"
                >
                    다음
                </Button>
            </div>
        </div>
    );
}
