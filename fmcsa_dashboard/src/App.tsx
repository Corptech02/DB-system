import React, { useState } from 'react';
import { Search, TrendingUp, Download, Users, AlertTriangle, Calendar } from 'lucide-react';
import SearchForm from './components/SearchForm';
import ResultsTable from './components/ResultsTable';
import StatsDashboard from './components/StatsDashboard';
import LeadsView from './components/LeadsView';
import ExportModal from './components/ExportModal';
import { SearchFilters } from './types';

type ViewType = 'search' | 'stats' | 'leads';

function App() {
  const [currentView, setCurrentView] = useState<ViewType>('search');
  const [searchFilters, setSearchFilters] = useState<SearchFilters>({});
  const [showExportModal, setShowExportModal] = useState(false);
  
  const handleSearch = (filters: SearchFilters) => {
    console.log('App.tsx - Search filters updated:', filters);
    setSearchFilters(filters);
  };
  
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">
                FMCSA Carrier Management
              </h1>
            </div>
            
            <nav className="flex space-x-4">
              <button
                onClick={() => setCurrentView('search')}
                className={`flex items-center px-3 py-2 text-sm font-medium rounded-md ${
                  currentView === 'search'
                    ? 'bg-primary-100 text-primary-700'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <Search className="w-4 h-4 mr-2" />
                Search
              </button>
              
              <button
                onClick={() => setCurrentView('stats')}
                className={`flex items-center px-3 py-2 text-sm font-medium rounded-md ${
                  currentView === 'stats'
                    ? 'bg-primary-100 text-primary-700'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <TrendingUp className="w-4 h-4 mr-2" />
                Statistics
              </button>
              
              <button
                onClick={() => setCurrentView('leads')}
                className={`flex items-center px-3 py-2 text-sm font-medium rounded-md ${
                  currentView === 'leads'
                    ? 'bg-primary-100 text-primary-700'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <Users className="w-4 h-4 mr-2" />
                Leads
              </button>
              
              <button
                onClick={() => setShowExportModal(true)}
                className="flex items-center px-3 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 rounded-md"
              >
                <Download className="w-4 h-4 mr-2" />
                Export
              </button>
            </nav>
          </div>
        </div>
      </header>
      
      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {currentView === 'search' && (
          <div className="space-y-6">
            <SearchForm onSearch={handleSearch} />
            <ResultsTable filters={searchFilters} />
          </div>
        )}
        
        {currentView === 'stats' && <StatsDashboard />}
        
        {currentView === 'leads' && <LeadsView />}
      </main>
      
      {/* Export Modal */}
      {showExportModal && (
        <ExportModal
          filters={searchFilters}
          onClose={() => setShowExportModal(false)}
        />
      )}
    </div>
  );
}

export default App;