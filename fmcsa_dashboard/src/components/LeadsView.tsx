import React, { useState, useEffect } from 'react';
import { useQuery } from 'react-query';
import { Phone, Mail, Calendar, TrendingUp, AlertCircle, Download, Filter, Search, Building, Truck, Shield, DollarSign, MapPin, Users, Target, FileSpreadsheet, CheckCircle, XCircle, Clock } from 'lucide-react';
import { format } from 'date-fns';
import api from '../services/api';

interface LeadFilters {
  state?: string;
  insuranceExpiringDays?: number;
  insuranceCompanies?: string[];
  minPowerUnits?: number;
  maxPowerUnits?: number;
  minDrivers?: number;
  safetyRating?: string;
  operatingStatus?: string;
  hazmatOnly?: boolean;
  leadScore?: string;
}

const LeadsView: React.FC = () => {
  const [filters, setFilters] = useState<LeadFilters>({
    insuranceExpiringDays: 90,
    // Remove default operating status to get all carriers
  });
  
  const [selectedLeads, setSelectedLeads] = useState<Set<number>>(new Set());
  const [showFilters, setShowFilters] = useState(true);
  const [availableInsuranceCompanies] = useState<string[]>([
    "Progressive Commercial",
    "Nationwide E&S/Specialty",
    "Great West Casualty Company",
    "Canal Insurance Company",
    "Sentry Insurance",
    "Northland Insurance Company",
    "Zurich North America",
    "The Hartford",
    "Liberty Mutual",
    "Travelers",
    "State Farm Commercial",
    "GEICO Commercial",
    "Allstate Business Insurance",
    "CNA Insurance",
    "Chubb",
    "AIG",
    "Berkshire Hathaway GUARD",
    "Farmers Insurance",
    "USAA Commercial",
    "American Family Insurance",
    "Auto-Owners Insurance",
    "Cincinnati Insurance",
    "Hanover Insurance Group",
    "Kemper",
    "Mercury Insurance",
    "MetLife Auto & Home",
    "QBE North America",
    "Selective Insurance",
    "Westfield Insurance",
    "Acuity Insurance"
  ]);
  
  // Fetch leads based on filters
  const { data: searchData, isLoading, refetch } = useQuery(
    ['leads', filters],
    async () => {
      // Use the search API with insurance filter
      const response = await api.searchCarriers({
        state: filters.state,
        insurance_expiring_days: filters.insuranceExpiringDays,
        insurance_companies: filters.insuranceCompanies,
        min_power_units: filters.minPowerUnits,
        max_power_units: filters.maxPowerUnits,
        min_drivers: filters.minDrivers,
        safety_rating: filters.safetyRating,
        operating_status: filters.operatingStatus,
        hazmat_only: filters.hazmatOnly,
      } as any, 1, 1000); // Get up to 1000 leads
      
      return response;
    },
    {
      keepPreviousData: true,
    }
  );
  
  // Calculate lead score based on various factors
  const calculateLeadScore = (carrier: any) => {
    let score = 50; // Base score
    
    // Insurance expiration urgency
    if (carrier.liability_insurance_date) {
      const today = new Date();
      const insuranceDate = new Date(carrier.liability_insurance_date);
      const daysDiff = Math.floor((insuranceDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
      
      if (daysDiff < 0) score += 30; // Expired = high priority
      else if (daysDiff <= 30) score += 20;
      else if (daysDiff <= 60) score += 10;
    }
    
    // Fleet size (larger = higher value)
    const powerUnits = carrier.power_units || 0;
    if (powerUnits > 50) score += 20;
    else if (powerUnits > 20) score += 15;
    else if (powerUnits > 10) score += 10;
    else if (powerUnits > 5) score += 5;
    
    // Safety rating
    if (carrier.safety_rating === 'SATISFACTORY') score += 10;
    else if (carrier.safety_rating === 'CONDITIONAL') score -= 5;
    else if (carrier.safety_rating === 'UNSATISFACTORY') score -= 15;
    
    // Has contact info
    if (carrier.phone || carrier.telephone) score += 5;
    if (carrier.email_address) score += 10;
    if (carrier.cell_phone) score += 5;
    
    return Math.min(100, Math.max(0, score));
  };
  
  const getLeadPriority = (score: number) => {
    if (score >= 80) return { label: 'HOT', color: 'text-red-600 bg-red-100', icon: '🔥' };
    if (score >= 60) return { label: 'WARM', color: 'text-orange-600 bg-orange-100', icon: '🌟' };
    if (score >= 40) return { label: 'COOL', color: 'text-blue-600 bg-blue-100', icon: '❄️' };
    return { label: 'COLD', color: 'text-gray-600 bg-gray-100', icon: '🧊' };
  };
  
  const exportLeads = (exportFormat: 'csv' | 'json') => {
    if (!searchData?.carriers || searchData.carriers.length === 0) {
      alert('No leads to export. Please generate leads first.');
      return;
    }
    
    const leadsToExport = searchData.carriers
      .filter(c => selectedLeads.size === 0 || selectedLeads.has(c.usdot_number))
      .map(carrier => {
        const score = calculateLeadScore(carrier);
        const priority = getLeadPriority(score);
        
        return {
          usdot_number: carrier.usdot_number,
          legal_name: carrier.legal_name,
          dba_name: carrier.dba_name || '',
          score: score,
          priority: priority.label,
          phone: carrier.phone || carrier.telephone || '',
          cell_phone: carrier.cell_phone || '',
          email: carrier.email_address || '',
          address: carrier.phy_street || carrier.physical_address || '',
          city: carrier.phy_city || carrier.physical_city || '',
          state: carrier.phy_state || carrier.physical_state || '',
          zip: carrier.phy_zip || carrier.physical_zip || '',
          power_units: carrier.power_units || 0,
          drivers: carrier.total_drivers || carrier.drivers || 0,
          safety_rating: carrier.safety_rating || '',
          insurance_expiry: carrier.liability_insurance_date || '',
          insurance_company: carrier.insurance_company || '',
          insurance_amount: carrier.liability_insurance_amount || '',
          hazmat: carrier.hazmat_flag || carrier.hm_ind === 'Y' ? 'Yes' : 'No',
          operating_status: carrier.operating_status || carrier.status_code || '',
        };
      });
    
    if (leadsToExport.length === 0) {
      alert('No leads selected for export.');
      return;
    }
    
    // Generate timestamp for filename
    const now = new Date();
    const timestamp = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
    
    try {
      if (exportFormat === 'csv') {
        // Convert to CSV
        const headers = Object.keys(leadsToExport[0]).join(',');
        const rows = leadsToExport.map(lead => 
          Object.values(lead).map(v => {
            // Handle null/undefined
            if (v === null || v === undefined) return '';
            // Quote strings that contain commas, quotes, or newlines
            if (typeof v === 'string' && (v.includes(',') || v.includes('"') || v.includes('\n'))) {
              return `"${v.replace(/"/g, '""')}"`;
            }
            return v;
          }).join(',')
        );
        const csv = [headers, ...rows].join('\n');
        
        // Download CSV
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `insurance_leads_${timestamp}.csv`;
        document.body.appendChild(a);
        a.click();
        setTimeout(() => {
          document.body.removeChild(a);
          window.URL.revokeObjectURL(url);
        }, 100);
      } else {
        // Download JSON
        const blob = new Blob([JSON.stringify(leadsToExport, null, 2)], { type: 'application/json;charset=utf-8;' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `insurance_leads_${timestamp}.json`;
        document.body.appendChild(a);
        a.click();
        setTimeout(() => {
          document.body.removeChild(a);
          window.URL.revokeObjectURL(url);
        }, 100);
      }
      
      console.log(`Exported ${leadsToExport.length} leads as ${exportFormat.toUpperCase()}`);
    } catch (error) {
      console.error('Export failed:', error);
      alert(`Failed to export leads: ${error.message}`);
    }
  };
  
  const states = [
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY',
  ];
  
  const leads = searchData?.carriers || [];
  const leadsWithScores = leads.map(carrier => ({
    ...carrier,
    leadScore: calculateLeadScore(carrier),
  })).sort((a, b) => b.leadScore - a.leadScore);
  
  // Statistics
  const stats = {
    total: leads.length,
    hot: leadsWithScores.filter(l => l.leadScore >= 80).length,
    warm: leadsWithScores.filter(l => l.leadScore >= 60 && l.leadScore < 80).length,
    cool: leadsWithScores.filter(l => l.leadScore >= 40 && l.leadScore < 60).length,
    cold: leadsWithScores.filter(l => l.leadScore < 40).length,
    withPhone: leads.filter(l => l.phone || l.telephone || l.cell_phone).length,
    withEmail: leads.filter(l => l.email_address).length,
    avgFleetSize: leads.reduce((acc, l) => acc + (l.power_units || 0), 0) / (leads.length || 1),
  };
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <Target className="w-8 h-8 text-primary-600" />
              Lead Generation Center
            </h1>
            <p className="text-gray-600 mt-2">
              Find and export high-value insurance leads based on expiration dates and business metrics
            </p>
          </div>
          
          <div className="flex gap-2">
            <button
              onClick={() => exportLeads('csv')}
              disabled={leads.length === 0}
              className="btn btn-primary flex items-center gap-2"
            >
              <FileSpreadsheet className="w-4 h-4" />
              Export CSV
            </button>
            <button
              onClick={() => exportLeads('json')}
              disabled={leads.length === 0}
              className="btn btn-secondary flex items-center gap-2"
            >
              <Download className="w-4 h-4" />
              Export JSON
            </button>
          </div>
        </div>
      </div>
      
      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow-sm p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Leads</p>
              <p className="text-2xl font-bold text-gray-900">{stats.total.toLocaleString()}</p>
            </div>
            <Users className="w-8 h-8 text-primary-600" />
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Hot Leads 🔥</p>
              <p className="text-2xl font-bold text-red-600">{stats.hot.toLocaleString()}</p>
            </div>
            <TrendingUp className="w-8 h-8 text-red-600" />
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">With Contact</p>
              <p className="text-2xl font-bold text-green-600">
                {Math.round((stats.withPhone / (stats.total || 1)) * 100)}%
              </p>
            </div>
            <Phone className="w-8 h-8 text-green-600" />
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Avg Fleet Size</p>
              <p className="text-2xl font-bold text-blue-600">
                {Math.round(stats.avgFleetSize)}
              </p>
            </div>
            <Truck className="w-8 h-8 text-blue-600" />
          </div>
        </div>
      </div>
      
      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Filter className="w-5 h-5" />
            Lead Filters
          </h2>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="text-primary-600 hover:text-primary-700"
          >
            {showFilters ? 'Hide' : 'Show'} Filters
          </button>
        </div>
        
        {showFilters && (
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {/* State Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                State
              </label>
              <select
                value={filters.state || ''}
                onChange={(e) => setFilters({ ...filters, state: e.target.value || undefined })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="">All States</option>
                {states.map(state => (
                  <option key={state} value={state}>{state}</option>
                ))}
              </select>
            </div>
            
            {/* Insurance Expiring Days */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Insurance Expiring (Days)
              </label>
              <select
                value={filters.insuranceExpiringDays || 90}
                onChange={(e) => setFilters({ ...filters, insuranceExpiringDays: Number(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
              >
                <option value={30}>Next 30 Days</option>
                <option value={60}>Next 60 Days</option>
                <option value={90}>Next 90 Days</option>
                <option value={180}>Next 6 Months</option>
                <option value={365}>Next Year</option>
                <option value={-30}>Already Expired</option>
              </select>
            </div>
            
            {/* Insurance Companies */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Insurance Companies (Select Multiple)
              </label>
              <div className="border border-gray-300 rounded-md p-2 max-h-32 overflow-y-auto">
                <div className="flex flex-wrap gap-2">
                  {availableInsuranceCompanies.map(company => (
                    <label key={company} className="flex items-center text-sm">
                      <input
                        type="checkbox"
                        checked={filters.insuranceCompanies?.includes(company) || false}
                        onChange={(e) => {
                          const companies = filters.insuranceCompanies || [];
                          if (e.target.checked) {
                            setFilters({ ...filters, insuranceCompanies: [...companies, company] });
                          } else {
                            setFilters({ ...filters, insuranceCompanies: companies.filter(c => c !== company) });
                          }
                        }}
                        className="mr-1 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                      />
                      <span className="whitespace-nowrap">{company}</span>
                    </label>
                  ))}
                </div>
              </div>
              {filters.insuranceCompanies && filters.insuranceCompanies.length > 0 && (
                <div className="mt-1 text-xs text-gray-600">
                  {filters.insuranceCompanies.length} companies selected
                  <button
                    onClick={() => setFilters({ ...filters, insuranceCompanies: undefined })}
                    className="ml-2 text-primary-600 hover:text-primary-700"
                  >
                    Clear all
                  </button>
                </div>
              )}
            </div>
            
            {/* Fleet Size */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Min Fleet Size
              </label>
              <input
                type="number"
                value={filters.minPowerUnits || ''}
                onChange={(e) => setFilters({ ...filters, minPowerUnits: e.target.value ? Number(e.target.value) : undefined })}
                placeholder="e.g., 10"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Max Fleet Size
              </label>
              <input
                type="number"
                value={filters.maxPowerUnits || ''}
                onChange={(e) => setFilters({ ...filters, maxPowerUnits: e.target.value ? Number(e.target.value) : undefined })}
                placeholder="e.g., 100"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
            
            {/* Driver Count */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Min Drivers
              </label>
              <input
                type="number"
                value={filters.minDrivers || ''}
                onChange={(e) => setFilters({ ...filters, minDrivers: e.target.value ? Number(e.target.value) : undefined })}
                placeholder="e.g., 5"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
            
            {/* Safety Rating */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Safety Rating
              </label>
              <select
                value={filters.safetyRating || ''}
                onChange={(e) => setFilters({ ...filters, safetyRating: e.target.value || undefined })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="">Any Rating</option>
                <option value="SATISFACTORY">Satisfactory</option>
                <option value="CONDITIONAL">Conditional</option>
                <option value="UNSATISFACTORY">Unsatisfactory</option>
              </select>
            </div>
            
            {/* Operating Status */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Operating Status
              </label>
              <select
                value={filters.operatingStatus || ''}
                onChange={(e) => setFilters({ ...filters, operatingStatus: e.target.value || undefined })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="">Any Status</option>
                <option value="ACTIVE">Active Only</option>
                <option value="INACTIVE">Inactive</option>
              </select>
            </div>
            
            {/* HazMat */}
            <div className="flex items-end">
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={filters.hazmatOnly || false}
                  onChange={(e) => setFilters({ ...filters, hazmatOnly: e.target.checked })}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="text-sm font-medium text-gray-700">HazMat Only</span>
              </label>
            </div>
          </div>
        )}
        
        <div className="mt-4 flex justify-end">
          <button
            onClick={() => refetch()}
            className="btn btn-primary flex items-center gap-2"
          >
            <Search className="w-4 h-4" />
            Generate Leads
          </button>
        </div>
      </div>
      
      {/* Lead Score Distribution */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-lg font-semibold mb-4">Lead Quality Distribution</h2>
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">🔥 Hot ({stats.hot})</span>
              <span className="text-sm text-gray-600">{stats.total ? Math.round((stats.hot / stats.total) * 100) : 0}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-4">
              <div
                className="bg-red-500 h-4 rounded-full"
                style={{ width: `${stats.total ? (stats.hot / stats.total) * 100 : 0}%` }}
              />
            </div>
          </div>
          
          <div className="flex-1">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">🌟 Warm ({stats.warm})</span>
              <span className="text-sm text-gray-600">{stats.total ? Math.round((stats.warm / stats.total) * 100) : 0}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-4">
              <div
                className="bg-orange-500 h-4 rounded-full"
                style={{ width: `${stats.total ? (stats.warm / stats.total) * 100 : 0}%` }}
              />
            </div>
          </div>
          
          <div className="flex-1">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">❄️ Cool ({stats.cool})</span>
              <span className="text-sm text-gray-600">{stats.total ? Math.round((stats.cool / stats.total) * 100) : 0}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-4">
              <div
                className="bg-blue-500 h-4 rounded-full"
                style={{ width: `${stats.total ? (stats.cool / stats.total) * 100 : 0}%` }}
              />
            </div>
          </div>
        </div>
      </div>
      
      {/* Leads Table */}
      <div className="bg-white rounded-lg shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">
              Generated Leads ({leadsWithScores.length})
            </h2>
            <div className="flex items-center gap-2">
              <button
                onClick={() => {
                  if (selectedLeads.size === leads.length) {
                    setSelectedLeads(new Set());
                  } else {
                    setSelectedLeads(new Set(leads.map(l => l.usdot_number)));
                  }
                }}
                className="text-sm text-primary-600 hover:text-primary-700"
              >
                {selectedLeads.size === leads.length ? 'Deselect All' : 'Select All'}
              </button>
              {selectedLeads.size > 0 && (
                <span className="text-sm text-gray-600">
                  {selectedLeads.size} selected
                </span>
              )}
            </div>
          </div>
        </div>
        
        {isLoading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          </div>
        ) : leadsWithScores.length === 0 ? (
          <div className="text-center py-12">
            <Target className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">No leads found. Adjust your filters and try again.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    <input
                      type="checkbox"
                      checked={selectedLeads.size === leads.length && leads.length > 0}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedLeads(new Set(leads.map(l => l.usdot_number)));
                        } else {
                          setSelectedLeads(new Set());
                        }
                      }}
                      className="rounded border-gray-300"
                    />
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Score
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Company
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Location
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Fleet
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Insurance
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Contact
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Safety
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {leadsWithScores.slice(0, 100).map((lead) => {
                  const priority = getLeadPriority(lead.leadScore);
                  const insuranceDays = lead.liability_insurance_date
                    ? Math.floor((new Date(lead.liability_insurance_date).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24))
                    : null;
                  
                  return (
                    <tr key={lead.usdot_number} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <input
                          type="checkbox"
                          checked={selectedLeads.has(lead.usdot_number)}
                          onChange={(e) => {
                            const newSelected = new Set(selectedLeads);
                            if (e.target.checked) {
                              newSelected.add(lead.usdot_number);
                            } else {
                              newSelected.delete(lead.usdot_number);
                            }
                            setSelectedLeads(newSelected);
                          }}
                          className="rounded border-gray-300"
                        />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-1 text-xs font-semibold rounded-full ${priority.color}`}>
                            {priority.icon} {lead.leadScore}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div>
                          <div className="text-sm font-medium text-gray-900">{lead.legal_name}</div>
                          {lead.dba_name && (
                            <div className="text-xs text-gray-500">DBA: {lead.dba_name}</div>
                          )}
                          <div className="text-xs text-gray-400">USDOT #{lead.usdot_number}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <div className="flex items-center gap-1">
                          <MapPin className="w-3 h-3" />
                          {lead.phy_city || lead.physical_city}, {lead.phy_state || lead.physical_state}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <div className="flex items-center gap-1">
                          <Truck className="w-3 h-3" />
                          {lead.power_units || 0} units
                        </div>
                        <div className="text-xs text-gray-500">
                          {lead.total_drivers || lead.drivers || 0} drivers
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {insuranceDays !== null && (
                          <div className={`text-sm font-medium ${
                            insuranceDays < 0 ? 'text-red-600' :
                            insuranceDays <= 30 ? 'text-orange-600' :
                            insuranceDays <= 60 ? 'text-yellow-600' :
                            'text-green-600'
                          }`}>
                            {insuranceDays < 0 ? `Expired ${Math.abs(insuranceDays)}d ago` :
                             insuranceDays === 0 ? 'Expires Today' :
                             `${insuranceDays}d`}
                          </div>
                        )}
                        {lead.insurance_company && (
                          <div className="text-xs text-gray-600 font-medium truncate max-w-[120px]">
                            {lead.insurance_company}
                          </div>
                        )}
                        {lead.liability_insurance_amount && (
                          <div className="text-xs text-gray-500">
                            ${(lead.liability_insurance_amount / 1000000).toFixed(1)}M
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 text-sm">
                        {(lead.phone || lead.telephone) && (
                          <div className="flex items-center gap-1 text-gray-600">
                            <Phone className="w-3 h-3" />
                            <span className="text-xs">{lead.phone || lead.telephone}</span>
                          </div>
                        )}
                        {lead.email_address && (
                          <div className="flex items-center gap-1 text-gray-600">
                            <Mail className="w-3 h-3" />
                            <span className="text-xs truncate max-w-[150px]">{lead.email_address}</span>
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {lead.safety_rating && (
                          <span className={`px-2 py-1 text-xs font-medium rounded ${
                            lead.safety_rating === 'SATISFACTORY' ? 'bg-green-100 text-green-800' :
                            lead.safety_rating === 'CONDITIONAL' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {lead.safety_rating[0]}
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
        
        {leadsWithScores.length > 100 && (
          <div className="px-6 py-3 bg-gray-50 text-center text-sm text-gray-600">
            Showing top 100 leads. Export to get all {leadsWithScores.length} leads.
          </div>
        )}
      </div>
    </div>
  );
};

export default LeadsView;