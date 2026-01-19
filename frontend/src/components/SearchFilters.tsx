import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { NativeSelect, NativeSelectOption } from '@/components/ui/native-select';

interface SearchFiltersProps {
    onSearch: (filters: {
        searchTerm: string;
        category: string;
        problemStockOnly: boolean;
    }) => void;
}

export function SearchFilters({ onSearch }: SearchFiltersProps) {
    const [searchTerm, setSearchTerm] = useState('');
    const [category, setCategory] = useState('');
    const [problemStockOnly, setProblemStockOnly] = useState(false);

    const handleSearch = () => {
        onSearch({ searchTerm, category, problemStockOnly });
    };

    return (
        <div className="flex gap-4 mb-6 flex-wrap items-center">
            <Input
                placeholder="검색 (SKU/제품명)"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="flex-1 min-w-[200px]"
            />

            <NativeSelect
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-[200px]"
            >
                <NativeSelectOption value="">카테고리 - 전체</NativeSelectOption>
                <NativeSelectOption value="전자제품">전자제품</NativeSelectOption>
                <NativeSelectOption value="식품">식품</NativeSelectOption>
                <NativeSelectOption value="의류">의류</NativeSelectOption>
            </NativeSelect>

            <div className="flex items-center gap-2">
                <Checkbox
                    id="problemStock"
                    checked={problemStockOnly}
                    onCheckedChange={(checked) => setProblemStockOnly(checked as boolean)}
                />
                <label
                    htmlFor="problemStock"
                    className="text-sm cursor-pointer select-none"
                >
                    문제 재고만 보기
                </label>
            </div>

            <Button onClick={handleSearch}>검색</Button>
        </div>
    );
}
