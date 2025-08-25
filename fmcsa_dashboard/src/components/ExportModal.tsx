import React, { useState } from 'react';
import { X, Download, FileText, FileSpreadsheet, CheckCircle } from 'lucide-react';
import { toast } from 'react-toastify';
import api from '../services/api';
import { SearchFilters, ExportRequest } from '../types';

interface ExportModalProps {
  filters: SearchFilters;
  onClose: () => void;
}

const ExportModal: React.FC<ExportModalProps> = ({ filters, onClose }) => {
  const [format, setFormat] = useState<'csv' | 'xlsx'>('csv');
  const [selectedColumns, setSelectedColumns] = useState<string[]>([
    'usdot_number',
    'legal_name',
    'dba_name',
    'physical_address',
    'physical_city',
    'physical_state',
    'physical_zip',
    'telephone',
    'email',
    'entity_type',
    'operating_status',
    'power_units',
    'drivers',
    'liability_insurance_date',
    'liability_insurance_amount',
    'safety_rating',
  ]);
  const [includeRawData, setIncludeRawData] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [exportComplete, setExportComplete] = useState(false);
  const [downloadUrl, setDownloadUrl] = useState<string>('');
  
  const availableColumns = [
    { key: 'usdot_number', label: 'USDOT Number' },
    { key: 'legal_name', label: 'Legal Name' },
    { key: 'dba_name', label: 'DBA Name' },
    { key: 'physical_address', label: 'Address' },
    { key: 'physical_city', label: 'City' },
    { key: 'physical_state', label: 'State' },
    { key: 'physical_zip', label: 'ZIP Code' },
    { key: 'mailing_address', label: 'Mailing Address' },
    { key: 'mailing_city', label: 'Mailing City' },
    { key: 'mailing_state', label: 'Mailing State' },
    { key: 'mailing_zip', label: 'Mailing ZIP' },
    { key: 'telephone', label: 'Phone' },
    { key: 'email', label: 'Email' },
    { key: 'entity_type', label: 'Entity Type' },
    { key: 'operating_status', label: 'Operating Status' },
    { key: 'power_units', label: 'Power Units' },
    { key: 'drivers', label: 'Drivers' },
    { key: 'hazmat_flag', label: 'Hazmat' },
    { key: 'liability_insurance_date', label: 'Insurance Date' },
    { key: 'liability_insurance_amount', label: 'Insurance Amount' },
    { key: 'safety_rating', label: 'Safety Rating' },
    { key: 'mcs_150_date', label: 'MCS-150 Date' },
    { key: 'cargo_carried', label: 'Cargo Carried' },
    { key: 'created_at', label: 'Created Date' },
    { key: 'updated_at', label: 'Updated Date' },
  ];
  
  const handleColumnToggle = (column: string) => {
    setSelectedColumns((prev) =>
      prev.includes(column)
        ? prev.filter((c) => c !== column)
        : [...prev, column]
    );
  };
  
  const handleSelectAll = () => {
    if (selectedColumns.length === availableColumns.length) {
      setSelectedColumns([]);
    } else {
      setSelectedColumns(availableColumns.map((c) => c.key));
    }
  };
  
  const handleExport = async () => {
    setIsExporting(true);
    
    try {
      const exportRequest: ExportRequest = {
        format,
        filters,
        columns: selectedColumns,
        include_raw_data: includeRawData,
      };
      
      const response = await api.createExport(exportRequest);
      
      setDownloadUrl(response.download_url);
      setExportComplete(true);
      
      toast.success(`Export completed! ${response.row_count.toLocaleString()} records exported.`);
      
      // Automatically download
      window.open(response.download_url, '_blank');
    } catch (error) {
      console.error('Export failed:', error);
      toast.error('Export failed. Please try again.');
    } finally {
      setIsExporting(false);
    }
  };
  
  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex justify-between items-center px-6 py-4 border-b">
          <h2 className="text-xl font-semibold">Export Carrier Data</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-500"
          >
            <X className="w-6 h-6" />
          </button>
        </div>
        
        {/* Content */}
        <div className="px-6 py-4 overflow-y-auto max-h-[calc(90vh-140px)]">
          {!exportComplete ? (
            <>
              {/* Format Selection */}
              <div className="mb-6">
                <label className="label">Export Format</label>
                <div className="grid grid-cols-2 gap-4">
                  <button
                    onClick={() => setFormat('csv')}
                    className={`p-4 border rounded-lg flex items-center justify-center ${
                      format === 'csv'
                        ? 'border-primary-500 bg-primary-50'
                        : 'border-gray-300 hover:border-gray-400'
                    }`}
                  >
                    <FileText className="w-6 h-6 mr-2" />
                    <div>
                      <div className="font-medium">CSV</div>
                      <div className="text-xs text-gray-500">
                        Up to 1M rows
                      </div>
                    </div>
                  </button>
                  
                  <button
                    onClick={() => setFormat('xlsx')}
                    className={`p-4 border rounded-lg flex items-center justify-center ${
                      format === 'xlsx'
                        ? 'border-primary-500 bg-primary-50'
                        : 'border-gray-300 hover:border-gray-400'
                    }`}
                  >
                    <FileSpreadsheet className="w-6 h-6 mr-2" />
                    <div>
                      <div className="font-medium">Excel</div>
                      <div className="text-xs text-gray-500">
                        Up to 1,048,576 rows
                      </div>
                    </div>
                  </button>
                </div>
              </div>
              
              {/* Column Selection */}
              <div className="mb-6">
                <div className="flex justify-between items-center mb-2">
                  <label className="label">Select Columns</label>
                  <button
                    onClick={handleSelectAll}
                    className="text-sm text-primary-600 hover:text-primary-700"
                  >
                    {selectedColumns.length === availableColumns.length
                      ? 'Deselect All'
                      : 'Select All'}
                  </button>
                </div>
                <div className="grid grid-cols-2 gap-2 max-h-64 overflow-y-auto border rounded-lg p-3">
                  {availableColumns.map((column) => (
                    <label
                      key={column.key}
                      className="flex items-center text-sm"
                    >
                      <input
                        type="checkbox"
                        checked={selectedColumns.includes(column.key)}
                        onChange={() => handleColumnToggle(column.key)}
                        className="rounded border-gray-300 text-primary-600 shadow-sm focus:border-primary-500 focus:ring focus:ring-primary-200 focus:ring-opacity-50"
                      />
                      <span className="ml-2">{column.label}</span>
                    </label>
                  ))}
                </div>
              </div>
              
              {/* Additional Options */}
              <div className="mb-6">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={includeRawData}
                    onChange={(e) => setIncludeRawData(e.target.checked)}
                    className="rounded border-gray-300 text-primary-600 shadow-sm focus:border-primary-500 focus:ring focus:ring-primary-200 focus:ring-opacity-50"
                  />
                  <span className="ml-2 text-sm text-gray-700">
                    Include raw data (JSON format)
                  </span>
                </label>
              </div>
              
              {/* Export Info */}
              <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-600">
                <p className="mb-2">
                  <strong>Export will include:</strong>
                </p>
                <ul className="list-disc list-inside space-y-1">
                  {Object.entries(filters).filter(([_, v]) => v).length > 0 ? (
                    <li>
                      Carriers matching current filters (
                      {Object.entries(filters)
                        .filter(([_, v]) => v)
                        .map(([k, v]) => `${k}: ${v}`)
                        .join(', ')}
                      )
                    </li>
                  ) : (
                    <li>All carriers in the database</li>
                  )}
                  <li>{selectedColumns.length} selected columns</li>
                  <li>Format: {format.toUpperCase()}</li>
                </ul>
              </div>
            </>
          ) : (
            <div className="text-center py-8">
              <CheckCircle className="w-16 h-16 text-success-500 mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">Export Complete!</h3>
              <p className="text-gray-600 mb-4">
                Your export has been generated successfully.
              </p>
              {downloadUrl && (
                <a
                  href={downloadUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn btn-primary"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Download Export
                </a>
              )}
            </div>
          )}
        </div>
        
        {/* Footer */}
        <div className="px-6 py-4 border-t flex justify-end space-x-3">
          <button onClick={onClose} className="btn btn-secondary">
            {exportComplete ? 'Close' : 'Cancel'}
          </button>
          {!exportComplete && (
            <button
              onClick={handleExport}
              disabled={isExporting || selectedColumns.length === 0}
              className="btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isExporting ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Exporting...
                </>
              ) : (
                <>
                  <Download className="w-4 h-4 mr-2" />
                  Export
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ExportModal;