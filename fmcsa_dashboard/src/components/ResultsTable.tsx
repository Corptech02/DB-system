import React, { useState, useMemo } from 'react';
import { useQuery } from 'react-query';
import { ChevronLeft, ChevronRight, ExternalLink, AlertCircle, CheckCircle, XCircle, X, Phone, Mail, MapPin, Truck, Users, Shield, Calendar, Building } from 'lucide-react';
import { format } from 'date-fns';
import api from '../services/api';
import { SearchFilters, Carrier } from '../types';
import CarrierProfile from './CarrierProfile';
import SimpleModal from './SimpleModal';
import ComprehensiveCarrierProfile from './ComprehensiveCarrierProfile';

interface ResultsTableProps {
  filters: SearchFilters;
}

const ResultsTable: React.FC<ResultsTableProps> = ({ filters }) => {
  const [page, setPage] = useState(1);
  const [perPage] = useState(20);
  const [selectedCarrier, setSelectedCarrier] = useState<Carrier | null>(null);
  
  // Debug effect to log when selectedCarrier changes
  React.useEffect(() => {
    console.log('Selected carrier changed:', selectedCarrier);
  }, [selectedCarrier]);
  
  const { data, isLoading, error } = useQuery(
    ['carriers', filters, page, perPage],
    () => {
      console.log('Fetching carriers with filters:', filters);
      return api.searchCarriers(filters, page, perPage);
    },
    {
      keepPreviousData: true,
      onError: (err) => {
        console.error('Search error:', err);
      },
      onSuccess: (data) => {
        console.log('Search results:', data);
      }
    }
  );
  
  const getInsuranceStatus = (date: string | undefined) => {
    if (!date) return { status: 'unknown', color: 'gray' };
    
    const insuranceDate = new Date(date);
    const today = new Date();
    const daysDiff = Math.floor((insuranceDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
    
    if (daysDiff < 0) return { status: 'expired', color: 'danger' };
    if (daysDiff <= 30) return { status: 'expiring', color: 'warning' };
    if (daysDiff <= 90) return { status: 'attention', color: 'yellow' };
    return { status: 'valid', color: 'success' };
  };
  
  const getOperatingStatusIcon = (status: string) => {
    switch (status) {
      case 'ACTIVE':
        return <CheckCircle className="w-4 h-4 text-success-500" />;
      case 'INACTIVE':
        return <XCircle className="w-4 h-4 text-gray-400" />;
      case 'OUT_OF_SERVICE':
        return <AlertCircle className="w-4 h-4 text-danger-500" />;
      default:
        return null;
    }
  };
  
  if (isLoading) {
    return (
      <div className="card">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="card">
        <div className="flex items-center text-danger-600">
          <AlertCircle className="w-5 h-5 mr-2" />
          Error loading carriers. Please try again.
        </div>
      </div>
    );
  }
  
  if (!data || data.carriers.length === 0) {
    return (
      <div className="card">
        <div className="text-center py-12">
          <p className="text-gray-500">No carriers found matching your criteria.</p>
        </div>
      </div>
    );
  }
  
  return (
    <>
      {/* Comprehensive Carrier Profile Modal */}
      {selectedCarrier && (
        <ComprehensiveCarrierProfile
          carrier={selectedCarrier}
          onClose={() => {
            console.log('Closing carrier profile');
            setSelectedCarrier(null);
          }}
        />
      )}
      
      <div className="card overflow-hidden">
      {/* Results Summary */}
      <div className="mb-4 flex justify-between items-center">
        <div>
          <p className="text-sm text-gray-600">
            Showing {((page - 1) * perPage) + 1} - {Math.min(page * perPage, data.total)} of {data.total.toLocaleString()} results
          </p>
          <p className="text-xs text-gray-500">Query time: {data.query_time_ms}ms</p>
        </div>
      </div>
      
      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                USDOT #
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Company Name
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Location
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Fleet Size
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Insurance
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Safety
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {data.carriers.map((carrier: Carrier) => {
              const insuranceStatus = getInsuranceStatus(carrier.liability_insurance_date);
              
              return (
                <tr key={carrier.usdot_number} className="hover:bg-gray-50">
                  <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                    {carrier.usdot_number}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-900">
                    <div>
                      <div className="font-medium">{carrier.legal_name}</div>
                      {carrier.dba_name && (
                        <div className="text-xs text-gray-500">DBA: {carrier.dba_name}</div>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                    {carrier.physical_city}, {carrier.physical_state}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <div className="flex items-center">
                      {getOperatingStatusIcon(carrier.operating_status)}
                      <span className="ml-2 text-sm text-gray-900">
                        {carrier.operating_status}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                    <div>
                      {carrier.power_units && (
                        <div>Units: {carrier.power_units}</div>
                      )}
                      {carrier.drivers && (
                        <div>Drivers: {carrier.drivers}</div>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <div className="flex items-center">
                      <span className={`badge badge-${insuranceStatus.color}`}>
                        {insuranceStatus.status}
                      </span>
                      {carrier.liability_insurance_date && (
                        <span className="ml-2 text-xs text-gray-500">
                          {format(new Date(carrier.liability_insurance_date), 'MM/dd/yy')}
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    {carrier.safety_rating ? (
                      <span className={`badge ${
                        carrier.safety_rating === 'SATISFACTORY' ? 'badge-success' :
                        carrier.safety_rating === 'CONDITIONAL' ? 'badge-warning' :
                        'badge-danger'
                      }`}>
                        {carrier.safety_rating}
                      </span>
                    ) : (
                      <span className="text-sm text-gray-400">N/A</span>
                    )}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm">
                    <button
                      onClick={() => {
                        console.log('Carrier clicked:', carrier);
                        setSelectedCarrier(carrier);
                      }}
                      className="text-primary-600 hover:text-primary-900"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      
      {/* Pagination */}
      <div className="mt-4 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className="btn btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronLeft className="w-4 h-4" />
            Previous
          </button>
          
          <div className="flex items-center space-x-1">
            {Array.from({ length: Math.min(5, data.pages) }, (_, i) => {
              const pageNum = i + 1;
              return (
                <button
                  key={pageNum}
                  onClick={() => setPage(pageNum)}
                  className={`px-3 py-1 text-sm rounded ${
                    page === pageNum
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  {pageNum}
                </button>
              );
            })}
          </div>
          
          <button
            onClick={() => setPage(p => Math.min(data.pages, p + 1))}
            disabled={page === data.pages}
            className="btn btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
            <ChevronRight className="w-4 h-4 ml-1" />
          </button>
        </div>
        
        <div className="text-sm text-gray-600">
          Page {page} of {data.pages}
        </div>
      </div>
    </div>
    </>
  );
};

export default ResultsTable;