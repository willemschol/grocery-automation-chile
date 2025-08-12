import React, { useState } from 'react';
import { Upload, Search, ShoppingCart, CheckCircle, AlertCircle, Loader, Download } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Badge } from './components/ui/badge';
import './App.css';

function App() {
  const [uploadedFile, setUploadedFile] = useState(null);
  const [products, setProducts] = useState([]);
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [listId, setListId] = useState('');
  const [testProduct, setTestProduct] = useState('');
  const [testResults, setTestResults] = useState(null);

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setLoading(true);
    setUploadedFile(file);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/upload-csv`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      
      if (response.ok) {
        setProducts(data.products);
        setListId(data.list_id);
      } else {
        alert(`Error: ${data.detail}`);
      }
    } catch (error) {
      alert(`Error uploading file: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleTestSearch = async () => {
    if (!testProduct.trim()) return;

    setLoading(true);
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/search-product`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ product_name: testProduct }),
      });

      const data = await response.json();
      
      if (response.ok) {
        setTestResults(data);
      } else {
        alert(`Error: ${data.detail}`);
      }
    } catch (error) {
      alert(`Error searching product: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchAllProducts = async () => {
    if (!listId) return;

    setLoading(true);
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/search-all-products`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ list_id: listId }),
      });

      const data = await response.json();
      
      if (response.ok) {
        setSearchResults(data.results);
      } else {
        alert(`Error: ${data.detail}`);
      }
    } catch (error) {
      alert(`Error searching products: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const exportToExcel = async () => {
    try {
      setLoading(true);
      
      // Prepare data for export
      let exportData = {};
      
      if (testResults) {
        // Export test results
        exportData = {
          search_term: testResults.product_name || 'test_search',
          results: {
            'Jumbo': testResults.jumbo_results || [],
            'Lider': testResults.lider_results || []
          }
        };
      } else if (searchResults.length > 0) {
        // Export full search results
        exportData = {
          search_term: 'full_search',
          results: searchResults
        };
      } else {
        alert('No hay resultados para exportar');
        return;
      }
      
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/export-excel`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(exportData)
      });
      
      if (response.ok) {
        // Download the file
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `search_results_${new Date().getTime()}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        alert('¡Archivo Excel descargado exitosamente!');
      } else {
        const errorData = await response.json();
        alert(`Error exportando a Excel: ${errorData.error}`);
      }
    } catch (error) {
      console.error('Export error:', error);
      alert('Error exportando a Excel');
    } finally {
      setLoading(false);
    }
  };

  const formatPrice = (price) => {
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP',
      minimumFractionDigits: 0,
    }).format(price);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-lg shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-2 rounded-xl">
                <ShoppingCart className="h-8 w-8 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
                  Automatización Supermercados
                </h1>
                <p className="text-gray-600 text-sm">
                  Compara precios entre Jumbo y Lider automáticamente
                </p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* CSV Upload Section */}
          <Card className="bg-white/70 backdrop-blur-sm shadow-xl border-0">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Upload className="h-5 w-5" />
                <span>Cargar Lista de Productos</span>
              </CardTitle>
              <CardDescription>
                Sube un archivo CSV con tus productos (Columna 1: Nombre, Columna 2: Tamaño preferido)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-400 transition-colors">
                  <input
                    type="file"
                    accept=".csv"
                    onChange={handleFileUpload}
                    className="hidden"
                    id="csv-upload"
                  />
                  <label
                    htmlFor="csv-upload"
                    className="cursor-pointer flex flex-col items-center space-y-2"
                  >
                    <Upload className="h-12 w-12 text-gray-400" />
                    <span className="text-gray-600">
                      {uploadedFile ? uploadedFile.name : 'Seleccionar archivo CSV'}
                    </span>
                    {uploadedFile && (
                      <Badge variant="secondary" className="mt-2">
                        {products.length} productos encontrados
                      </Badge>
                    )}
                  </label>
                </div>

                {products.length > 0 && (
                  <Button
                    onClick={handleSearchAllProducts}
                    disabled={loading}
                    className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
                  >
                    {loading ? (
                      <Loader className="h-4 w-4 animate-spin mr-2" />
                    ) : (
                      <Search className="h-4 w-4 mr-2" />
                    )}
                    Buscar Todos los Productos
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Test Search Section */}
          <Card className="bg-white/70 backdrop-blur-sm shadow-xl border-0">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Search className="h-5 w-5" />
                <span>Prueba de Búsqueda</span>
              </CardTitle>
              <CardDescription>
                Prueba la búsqueda con un producto individual
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex space-x-2">
                  <Input
                    placeholder="Ej: Coca Cola, Pan, Leche..."
                    value={testProduct}
                    onChange={(e) => setTestProduct(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleTestSearch()}
                    className="flex-1"
                  />
                  <Button
                    onClick={handleTestSearch}
                    disabled={loading || !testProduct.trim()}
                    className="px-6"
                  >
                    {loading ? (
                      <Loader className="h-4 w-4 animate-spin" />
                    ) : (
                      <Search className="h-4 w-4" />
                    )}
                  </Button>
                </div>

                {testResults && (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-medium">Resultados para "{testResults.product_name}"</h4>
                        <Badge variant="outline">{testResults.total_found} productos encontrados</Badge>
                      </div>
                      <Button
                        onClick={exportToExcel}
                        disabled={loading}
                        size="sm"
                        className="bg-green-600 hover:bg-green-700 text-white"
                      >
                        {loading ? (
                          <Loader className="h-3 w-3 animate-spin mr-1" />
                        ) : (
                          <Download className="h-3 w-3 mr-1" />
                        )}
                        Excel
                      </Button>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <div className="p-3 bg-orange-50 rounded-lg border border-orange-200">
                        <div className="flex items-center justify-between mb-2">
                          <h5 className="font-medium text-orange-800">Jumbo</h5>
                          <Badge variant="secondary">{testResults.jumbo_results.length}</Badge>
                        </div>
                        {testResults.jumbo_results.slice(0, 2).map((product, idx) => (
                          <div key={idx} className="text-sm">
                            <div className="font-medium truncate">{product.name}</div>
                            <div className="text-orange-600">{formatPrice(product.price)}</div>
                          </div>
                        ))}
                      </div>

                      <div className="p-3 bg-red-50 rounded-lg border border-red-200">
                        <div className="flex items-center justify-between mb-2">
                          <h5 className="font-medium text-red-800">Lider</h5>
                          <Badge variant="secondary">{testResults.lider_results.length}</Badge>
                        </div>
                        {testResults.lider_results.slice(0, 2).map((product, idx) => (
                          <div key={idx} className="text-sm">
                            <div className="font-medium truncate">{product.name}</div>
                            <div className="text-red-600">{formatPrice(product.price)}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Products List */}
        {products.length > 0 && (
          <Card className="mt-8 bg-white/70 backdrop-blur-sm shadow-xl border-0">
            <CardHeader>
              <CardTitle>Lista de Productos Cargados</CardTitle>
              <CardDescription>
                {products.length} productos listos para buscar
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {products.map((product) => (
                  <div
                    key={product.id}
                    className="p-4 bg-gray-50 rounded-lg border border-gray-200"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-medium text-gray-900">{product.name}</h4>
                        <p className="text-sm text-gray-600">
                          Tamaño: {product.preferred_size}
                        </p>
                      </div>
                      <Badge variant="outline" className="ml-2">
                        {product.status}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Search Results */}
        {searchResults.length > 0 && (
          <Card className="mt-8 bg-white/70 backdrop-blur-sm shadow-xl border-0">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                  <div>
                    <CardTitle>Resultados de Búsqueda y Comparación</CardTitle>
                    <CardDescription>
                      Comparación de precios entre Jumbo y Lider
                    </CardDescription>
                  </div>
                </div>
                <Button
                  onClick={exportToExcel}
                  disabled={loading}
                  className="bg-green-600 hover:bg-green-700 text-white"
                >
                  {loading ? (
                    <Loader className="h-4 w-4 animate-spin mr-2" />
                  ) : (
                    <Download className="h-4 w-4 mr-2" />
                  )}
                  Exportar Excel
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {searchResults.map((result, idx) => (
                  <div
                    key={idx}
                    className="p-6 bg-gradient-to-r from-gray-50 to-gray-100 rounded-xl border border-gray-200"
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h4 className="text-lg font-semibold text-gray-900">
                          {result.product.name}
                        </h4>
                        <p className="text-sm text-gray-600">
                          Tamaño preferido: {result.product.preferred_size}
                        </p>
                      </div>
                      {result.cheaper_option && (
                        <Badge 
                          variant={result.cheaper_option.store === 'Jumbo' ? 'default' : 'destructive'}
                          className="text-sm"
                        >
                          Mejor opción: {result.cheaper_option.store}
                        </Badge>
                      )}
                    </div>

                    {result.error ? (
                      <div className="flex items-center space-x-2 text-red-600">
                        <AlertCircle className="h-4 w-4" />
                        <span className="text-sm">Error: {result.error}</span>
                      </div>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {/* Jumbo Results */}
                        <div className="p-4 bg-orange-50 rounded-lg border border-orange-200">
                          <div className="flex items-center justify-between mb-3">
                            <h5 className="font-medium text-orange-800">Jumbo</h5>
                            <Badge variant="outline">{result.jumbo_results.length} encontrados</Badge>
                          </div>
                          {result.best_jumbo ? (
                            <div className="space-y-2">
                              <div className="text-sm font-medium truncate">
                                {result.best_jumbo.name}
                              </div>
                              <div className="text-lg font-bold text-orange-600">
                                {formatPrice(result.best_jumbo.price)}
                              </div>
                            </div>
                          ) : (
                            <div className="text-sm text-gray-500">No encontrado</div>
                          )}
                        </div>

                        {/* Lider Results */}
                        <div className="p-4 bg-red-50 rounded-lg border border-red-200">
                          <div className="flex items-center justify-between mb-3">
                            <h5 className="font-medium text-red-800">Lider</h5>
                            <Badge variant="outline">{result.lider_results.length} encontrados</Badge>
                          </div>
                          {result.best_lider ? (
                            <div className="space-y-2">
                              <div className="text-sm font-medium truncate">
                                {result.best_lider.name}
                              </div>
                              <div className="text-lg font-bold text-red-600">
                                {formatPrice(result.best_lider.price)}
                              </div>
                            </div>
                          ) : (
                            <div className="text-sm text-gray-500">No encontrado</div>
                          )}
                        </div>
                      </div>
                    )}

                    {result.price_difference > 0 && (
                      <div className="mt-3 text-center">
                        <Badge variant="outline" className="text-sm">
                          Diferencia: {formatPrice(result.price_difference)}
                        </Badge>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  );
}

export default App;