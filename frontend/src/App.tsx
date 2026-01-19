import { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from '@/components/ui/toaster';
import { SearchFilters } from '@/components/SearchFilters';
import { SKUTable } from '@/components/SKUTable';
import { SKUForm } from '@/components/SKUForm';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';
import type { SKUResponse } from '@/types/sku';
import './App.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function AppContent() {
  const [searchTerm, setSearchTerm] = useState('');
  const [category, setCategory] = useState('');
  const [problemStockOnly, setProblemStockOnly] = useState(false);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingSku, setEditingSku] = useState<SKUResponse | null>(null);

  const handleSearch = (filters: {
    searchTerm: string;
    category: string;
    problemStockOnly: boolean;
  }) => {
    setSearchTerm(filters.searchTerm);
    setCategory(filters.category);
    setProblemStockOnly(filters.problemStockOnly);
  };

  const handleCreate = () => {
    setEditingSku(null);
    setIsFormOpen(true);
  };

  const handleEdit = (sku: SKUResponse) => {
    setEditingSku(sku);
    setIsFormOpen(true);
  };

  const handleFormClose = () => {
    setIsFormOpen(false);
    setEditingSku(null);
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto p-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold">재고(SKU) 관리 시스템</h1>
          <Button onClick={handleCreate}>
            <Plus className="mr-2 h-4 w-4" />
            SKU 생성
          </Button>
        </div>

        <SearchFilters onSearch={handleSearch} />

        <SKUTable
          searchTerm={searchTerm}
          category={category}
          problemStockOnly={problemStockOnly}
          onEdit={handleEdit}
        />

        <SKUForm
          open={isFormOpen}
          onOpenChange={handleFormClose}
          sku={editingSku}
        />
      </div>
      <Toaster />
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}

export default App;
