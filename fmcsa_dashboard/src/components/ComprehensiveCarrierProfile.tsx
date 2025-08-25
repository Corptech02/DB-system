import React, { useState, useEffect } from 'react';
import { X, Phone, Mail, MapPin, Truck, Users, Shield, Calendar, Building, AlertTriangle, CheckCircle, FileText, Package, DollarSign, Activity, Info, Clock, Hash, Globe, Car, Bus, Clipboard, Loader2 } from 'lucide-react';
import { format } from 'date-fns';

interface ComprehensiveCarrierProfileProps {
  carrier: any;
  onClose: () => void;
}

const ComprehensiveCarrierProfile: React.FC<ComprehensiveCarrierProfileProps> = ({ carrier, onClose }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [carrierData, setCarrierData] = useState(carrier);
  const [isLoadingInsurance, setIsLoadingInsurance] = useState(true);
  const [insuranceData, setInsuranceData] = useState<any>(null);
  const [insuranceFetchFailed, setInsuranceFetchFailed] = useState(false);

  useEffect(() => {
    // Fetch fresh carrier data with insurance info
    const fetchCarrierDetails = async () => {
      setIsLoadingInsurance(true);
      setInsuranceFetchFailed(false);
      
      // Ensure loading state shows for at least 1 second
      const startTime = Date.now();
      
      try {
        const response = await fetch(`http://localhost:8000/api/carriers/${carrier.usdot_number || carrier.dot_number}`);
        if (response.ok) {
          const data = await response.json();
          setCarrierData(data);
          
          // Check if insurance data was actually fetched
          if (data.insurance_data_source && data.insurance_data_source.includes("Error")) {
            setInsuranceFetchFailed(true);
          } else if (data.insurance_data_source) {
            // We got a response from the L&I system (even if no insurance on file)
            setInsuranceData({
              liability_insurance_date: data.liability_insurance_date,
              liability_insurance_amount: data.liability_insurance_amount,
              insurance_company: data.insurance_company,
              insurance_data_source: data.insurance_data_source,
              insurance_data_type: data.insurance_data_type
            });
          }
        } else {
          setInsuranceFetchFailed(true);
        }
      } catch (error) {
        console.error('Error fetching carrier details:', error);
        setInsuranceFetchFailed(true);
      } finally {
        // Ensure loading was shown for at least 1 second
        const elapsed = Date.now() - startTime;
        if (elapsed < 1000) {
          setTimeout(() => setIsLoadingInsurance(false), 1000 - elapsed);
        } else {
          setIsLoadingInsurance(false);
        }
      }
    };

    fetchCarrierDetails();
  }, [carrier.usdot_number, carrier.dot_number]);
  
  // Get all available fields from the carrier object
  const allFields = Object.keys(carrier || {}).sort();
  
  // Helper function to format field names
  const formatFieldName = (field: string) => {
    return field
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (char) => char.toUpperCase())
      .replace('Usdot', 'USDOT')
      .replace('Dba', 'DBA')
      .replace('Mcs', 'MCS')
      .replace('Cdl', 'CDL')
      .replace('Hm', 'HazMat')
      .replace('Phy', 'Physical')
      .replace('Nbr', 'Number');
  };
  
  // Helper to format dates
  const formatDate = (date: string | undefined) => {
    if (!date) return 'N/A';
    try {
      // Handle YYYYMMDD format
      if (date.length === 8 && !date.includes('-')) {
        const year = date.substring(0, 4);
        const month = date.substring(4, 6);
        const day = date.substring(6, 8);
        return `${month}/${day}/${year}`;
      }
      return format(new Date(date), 'MM/dd/yyyy');
    } catch {
      return date;
    }
  };
  
  // Helper to display value with proper formatting
  const displayValue = (value: any) => {
    if (value === null || value === undefined || value === '') return 'N/A';
    if (typeof value === 'boolean') return value ? 'Yes' : 'No';
    if (typeof value === 'string' && value.length === 8 && !isNaN(Number(value))) {
      // Might be a date in YYYYMMDD format
      if (value.startsWith('19') || value.startsWith('20')) {
        return formatDate(value);
      }
    }
    return value;
  };

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Info },
    { id: 'fleet', label: 'Fleet & Equipment', icon: Truck },
    { id: 'safety', label: 'Safety & Compliance', icon: Shield },
    { id: 'business', label: 'Business Info', icon: Building },
    { id: 'cargo', label: 'Cargo & Operations', icon: Package },
    { id: 'contact', label: 'Contact & Location', icon: MapPin },
    { id: 'raw', label: 'All Data', icon: FileText }
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-2xl" style={{ width: '95%', maxWidth: '1400px', height: '90vh', display: 'flex', flexDirection: 'column' }}>
        
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white px-6 py-4 rounded-t-lg">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-3xl font-bold">{carrier.legal_name || 'Unknown Carrier'}</h1>
              {carrier.dba_name && (
                <p className="text-blue-100 mt-1 text-lg">DBA: {carrier.dba_name}</p>
              )}
              <div className="flex items-center gap-4 mt-2">
                <span className="bg-blue-500 bg-opacity-30 px-3 py-1 rounded-full text-sm">
                  USDOT #{carrier.usdot_number || carrier.dot_number}
                </span>
                {carrier.mc_mx_ff_number && (
                  <span className="bg-blue-500 bg-opacity-30 px-3 py-1 rounded-full text-sm">
                    MC #{carrier.mc_mx_ff_number}
                  </span>
                )}
                <span className={`px-3 py-1 rounded-full text-sm ${
                  carrier.operating_status === 'ACTIVE' ? 'bg-green-500 bg-opacity-30' :
                  carrier.operating_status === 'INACTIVE' ? 'bg-gray-500 bg-opacity-30' :
                  'bg-red-500 bg-opacity-30'
                }`}>
                  {carrier.operating_status || carrier.status_code || 'Unknown Status'}
                </span>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:text-blue-100 transition-colors"
            >
              <X className="w-8 h-8" />
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-gray-100 px-6 py-2 flex gap-2 overflow-x-auto">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-200'
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'overview' && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {/* Basic Information */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                  <Building className="w-5 h-5 text-blue-600" />
                  Basic Information
                </h3>
                <div className="space-y-2 text-sm">
                  <div><strong>Legal Name:</strong> {carrier.legal_name}</div>
                  <div><strong>DBA Name:</strong> {displayValue(carrier.dba_name)}</div>
                  <div><strong>USDOT Number:</strong> {carrier.usdot_number || carrier.dot_number}</div>
                  <div><strong>MC Number:</strong> {displayValue(carrier.docket1prefix === 'MC' ? carrier.docket1 : null)}</div>
                  <div><strong>MX Number:</strong> {displayValue(carrier.docket2prefix === 'MX' ? carrier.docket2 : null)}</div>
                  <div><strong>FF Number:</strong> {displayValue(carrier.docket3prefix === 'FF' ? carrier.docket3 : null)}</div>
                  <div><strong>Entity Type:</strong> {displayValue(carrier.entity_type || (carrier.carship === 'C' ? 'Carrier' : carrier.carship === 'S' ? 'Shipper' : carrier.carship === 'B' ? 'Broker' : carrier.carship))}</div>
                  <div><strong>Business Organization:</strong> {displayValue(carrier.business_org_desc)}</div>
                  <div><strong>Dun & Bradstreet:</strong> {displayValue(carrier.dun_bradstreet_no)}</div>
                  <div><strong>Operating Status:</strong> 
                    <span className={`ml-2 px-2 py-1 rounded text-xs ${
                      (carrier.operating_status === 'ACTIVE' || carrier.status_code === 'A') ? 'bg-green-100 text-green-800' :
                      (carrier.operating_status === 'INACTIVE' || carrier.status_code === 'I') ? 'bg-gray-100 text-gray-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {carrier.operating_status || (carrier.status_code === 'A' ? 'ACTIVE' : carrier.status_code === 'I' ? 'INACTIVE' : carrier.status_code)}
                    </span>
                  </div>
                  <div><strong>Carrier Operation:</strong> {displayValue(carrier.carrier_operation === 'A' ? 'Interstate' : carrier.carrier_operation === 'B' ? 'Intrastate (Hazmat)' : carrier.carrier_operation === 'C' ? 'Intrastate (Non-Hazmat)' : carrier.carrier_operation)}</div>
                  <div><strong>Fleet Size Category:</strong> {displayValue(carrier.fleetsize)}</div>
                </div>
              </div>

              {/* Fleet Summary */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                  <Truck className="w-5 h-5 text-blue-600" />
                  Fleet Summary
                </h3>
                <div className="space-y-2 text-sm">
                  <div><strong>Power Units:</strong> {carrier.power_units || '0'}</div>
                  <div><strong>Truck Units:</strong> {displayValue(carrier.truck_units)}</div>
                  <div><strong>Trailers (Owned):</strong> {displayValue(carrier.owntrail)}</div>
                  <div><strong>Trailers (Term Leased):</strong> {displayValue(carrier.trmtrail)}</div>
                  <div><strong>Total Drivers:</strong> {carrier.total_drivers || carrier.drivers || '0'}</div>
                  <div><strong>CDL Drivers:</strong> {displayValue(carrier.total_cdl)}</div>
                  <div><strong>Interstate Drivers:</strong> {displayValue(carrier.driver_inter_total)}</div>
                  <div><strong>Intrastate Drivers:</strong> {displayValue(carrier.total_intrastate_drivers)}</div>
                  <div><strong>HazMat:</strong> {carrier.hazmat_flag || carrier.hm_ind === 'Y' ? '✅ Yes' : '❌ No'}</div>
                </div>
              </div>

              {/* Important Dates */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                  <Calendar className="w-5 h-5 text-blue-600" />
                  Important Dates & Insurance
                </h3>
                <div className="space-y-2 text-sm">
                  {/* Insurance Alert at Top */}
                  {carrier.liability_insurance_date && (
                    <div className={`p-2 rounded font-semibold ${
                      (() => {
                        const today = new Date();
                        const insuranceDate = new Date(carrier.liability_insurance_date);
                        const daysDiff = Math.floor((insuranceDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
                        
                        if (daysDiff < 0) return 'bg-red-100 text-red-800';
                        if (daysDiff <= 30) return 'bg-orange-100 text-orange-800';
                        if (daysDiff <= 90) return 'bg-yellow-100 text-yellow-800';
                        return 'bg-green-100 text-green-800';
                      })()
                    }`}>
                      Insurance: {formatDate(carrier.liability_insurance_date)}
                      {(() => {
                        const today = new Date();
                        const insuranceDate = new Date(carrier.liability_insurance_date);
                        const daysDiff = Math.floor((insuranceDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
                        
                        if (daysDiff < 0) return ` (EXPIRED)`;
                        if (daysDiff <= 30) return ` (${daysDiff} days)`;
                        return '';
                      })()}
                    </div>
                  )}
                  
                  <div><strong>Added to FMCSA:</strong> {formatDate(carrier.add_date)}</div>
                  <div><strong>MCS-150 Updated:</strong> {formatDate(carrier.mcs150_date)}</div>
                  <div><strong>MCS-150 Mileage:</strong> {displayValue(carrier.mcs150_mileage)} miles</div>
                  <div><strong>MCS-150 Mileage Year:</strong> {displayValue(carrier.mcs150_mileage_year)}</div>
                  <div><strong>Safety Rating Date:</strong> {formatDate(carrier.safety_rating_date)}</div>
                  <div><strong>Review Date:</strong> {formatDate(carrier.review_date)}</div>
                  <div><strong>MCSIP Date:</strong> {formatDate(carrier.mcsipdate)}</div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'fleet' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Vehicle Inventory */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                  <Car className="w-5 h-5 text-blue-600" />
                  Vehicle Inventory
                </h3>
                <div className="space-y-2 text-sm">
                  <div className="font-semibold text-gray-700 mt-2">Owned Equipment:</div>
                  <div><strong>Tractors:</strong> {displayValue(carrier.owntract)}</div>
                  <div><strong>Trucks:</strong> {displayValue(carrier.owntruck)}</div>
                  <div><strong>Trailers:</strong> {displayValue(carrier.owntrail)}</div>
                  <div><strong>Buses (16+ passengers):</strong> {displayValue(carrier.ownbus_16)}</div>
                  <div><strong>School Buses (16+):</strong> {displayValue(carrier.ownschool_16)}</div>
                  <div><strong>School Buses (9-15):</strong> {displayValue(carrier.ownschool_9_15)}</div>
                  <div><strong>Vans (9-15 passengers):</strong> {displayValue(carrier.ownvan_9_15)}</div>
                  <div><strong>Vans (1-8 passengers):</strong> {displayValue(carrier.ownvan_1_8)}</div>
                  <div><strong>Limos (1-8 passengers):</strong> {displayValue(carrier.ownlimo_1_8)}</div>
                  <div><strong>Motor Coaches:</strong> {displayValue(carrier.owncoach)}</div>
                  
                  <div className="font-semibold text-gray-700 mt-3">Term Leased Equipment:</div>
                  <div><strong>Tractors:</strong> {displayValue(carrier.trmtract)}</div>
                  <div><strong>Trucks:</strong> {displayValue(carrier.trmtruck)}</div>
                  <div><strong>Trailers:</strong> {displayValue(carrier.trmtrail)}</div>
                  
                  <div className="font-semibold text-gray-700 mt-3">Trip Leased Equipment:</div>
                  <div><strong>Tractors:</strong> {displayValue(carrier.trptract)}</div>
                </div>
              </div>

              {/* Fleet Statistics */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                  <Activity className="w-5 h-5 text-blue-600" />
                  Fleet Statistics & Mileage
                </h3>
                <div className="space-y-2 text-sm">
                  <div><strong>Total Power Units:</strong> {displayValue(carrier.power_units)}</div>
                  <div><strong>Total Truck Units:</strong> {displayValue(carrier.truck_units)}</div>
                  <div><strong>Total Bus Units:</strong> {displayValue(carrier.bus_units)}</div>
                  <div><strong>Fleet Size Category:</strong> {displayValue(carrier.fleetsize)}</div>
                  
                  <div className="font-semibold text-gray-700 mt-3">Mileage Information:</div>
                  <div><strong>MCS-150 Mileage:</strong> {displayValue(carrier.mcs150_mileage)} miles</div>
                  <div><strong>MCS-150 Mileage Year:</strong> {displayValue(carrier.mcs150_mileage_year)}</div>
                  <div><strong>MCS-151 Mileage:</strong> {displayValue(carrier.mcs151_mileage)} miles</div>
                  
                  <div className="font-semibold text-gray-700 mt-3">Driver Information:</div>
                  <div><strong>Total Drivers:</strong> {displayValue(carrier.total_drivers)}</div>
                  <div><strong>CDL Drivers:</strong> {displayValue(carrier.total_cdl)}</div>
                  <div><strong>Interstate Drivers:</strong> {displayValue(carrier.driver_inter_total)}</div>
                  <div><strong>Intrastate Drivers:</strong> {displayValue(carrier.total_intrastate_drivers)}</div>
                  <div><strong>Avg Drivers Leased/Month:</strong> {displayValue(carrier.avg_drivers_leased_per_month)}</div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'safety' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                  <Shield className="w-5 h-5 text-blue-600" />
                  Safety & Compliance
                </h3>
                <div className="space-y-2 text-sm">
                  <div><strong>Safety Rating:</strong> 
                    <span className={`ml-2 px-2 py-1 rounded text-xs ${
                      carrierData.safety_rating === 'SATISFACTORY' || carrierData.safety_rating === 'S' ? 'bg-green-100 text-green-800' :
                      carrierData.safety_rating === 'CONDITIONAL' || carrierData.safety_rating === 'C' ? 'bg-yellow-100 text-yellow-800' :
                      carrierData.safety_rating === 'UNSATISFACTORY' ? 'bg-red-100 text-red-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {displayValue(carrierData.safety_rating)}
                    </span>
                  </div>
                  <div><strong>Safety Rating Date:</strong> {formatDate(carrierData.safety_rating_date)}</div>
                  <div><strong>Safety Investigation Territory:</strong> {displayValue(carrierData.safety_inv_terr)}</div>
                  <div><strong>Review Type:</strong> {displayValue(carrierData.review_type)}</div>
                  <div><strong>Review Date:</strong> {formatDate(carrierData.review_date)}</div>
                  <div><strong>Review ID:</strong> {displayValue(carrierData.review_id)}</div>
                  
                  <div className="font-semibold text-gray-700 mt-3">MCS-150 Information:</div>
                  <div><strong>Last Update:</strong> {formatDate(carrierData.mcs150_date)}</div>
                  <div><strong>Update Code:</strong> {displayValue(carrierData.mcs150_update_code_id)}</div>
                  <div><strong>MCSIP Date:</strong> {formatDate(carrierData.mcsipdate)}</div>
                  <div><strong>MCSIP Step:</strong> {displayValue(carrierData.mcsipstep)}</div>
                  
                  <div className="font-semibold text-gray-700 mt-3">HazMat Status:</div>
                  <div><strong>HazMat Flag:</strong> {carrierData.hm_flag === 'Y' || carrierData.hm_ind === 'Y' ? '✅ Authorized' : '❌ Not Authorized'}</div>
                  
                  <div className="font-semibold text-gray-700 mt-3">Prior Issues:</div>
                  <div><strong>Prior Revoke Flag:</strong> {displayValue(carrierData.prior_revoke_flag)}</div>
                  <div><strong>Prior Revoked DOT:</strong> {displayValue(carrierData.prior_revoke_dot_number)}</div>
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                  <FileText className="w-5 h-5 text-blue-600" />
                  Insurance & Liability
                  {insuranceData?.insurance_data_type === 'real' && (
                    <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">LIVE DATA</span>
                  )}
                </h3>
                
                {isLoadingInsurance ? (
                  <div className="py-12 flex flex-col items-center justify-center">
                    <Loader2 className="w-10 h-10 text-blue-600 animate-spin mb-4" />
                    <p className="text-blue-700 font-semibold text-lg">Fetching real-time insurance data...</p>
                    <p className="text-sm text-blue-600 mt-2">Connecting to FMCSA L&I System</p>
                    <p className="text-xs text-gray-500 mt-1">This may take a few seconds</p>
                  </div>
                ) : insuranceFetchFailed ? (
                  <div className="bg-red-50 border border-red-200 rounded p-4 text-sm">
                    <div className="flex items-start gap-2">
                      <AlertTriangle className="w-5 h-5 text-red-500 mt-0.5" />
                      <div>
                        <p className="font-semibold text-red-700">Insurance Data Unavailable</p>
                        <p className="text-red-600 mt-1">Unable to retrieve insurance information from FMCSA at this time.</p>
                        <p className="text-xs text-gray-600 mt-2">Alternative sources:</p>
                        <ul className="mt-1 ml-4 list-disc text-xs">
                          <li>Visit <a href="https://li-public.fmcsa.dot.gov/" target="_blank" className="underline">FMCSA L&I System</a></li>
                          <li>Check <a href="https://safer.fmcsa.dot.gov/CompanySnapshot.aspx" target="_blank" className="underline">SAFER Company Snapshot</a></li>
                        </ul>
                      </div>
                    </div>
                  </div>
                ) : (
                <div className="space-y-2 text-sm">
                  {/* Insurance Status Banner */}
                  {(insuranceData?.liability_insurance_date || carrierData.liability_insurance_date) && (
                    <div className={`p-3 rounded-lg border-2 ${
                      (() => {
                        const today = new Date();
                        const dateToUse = insuranceData?.liability_insurance_date || carrierData.liability_insurance_date;
                        const insuranceDate = new Date(dateToUse);
                        const daysDiff = Math.floor((insuranceDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
                        
                        if (daysDiff < 0) return 'bg-red-50 border-red-300';
                        if (daysDiff <= 30) return 'bg-orange-50 border-orange-300';
                        if (daysDiff <= 90) return 'bg-yellow-50 border-yellow-300';
                        return 'bg-green-50 border-green-300';
                      })()
                    }`}>
                      <div className="font-semibold">
                        {(() => {
                          const today = new Date();
                          const dateToUse = insuranceData?.liability_insurance_date || carrierData.liability_insurance_date;
                          const insuranceDate = new Date(dateToUse);
                          const daysDiff = Math.floor((insuranceDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
                          
                          if (daysDiff < 0) return `⚠️ EXPIRED ${Math.abs(daysDiff)} days ago`;
                          if (daysDiff === 0) return '⚠️ EXPIRES TODAY';
                          if (daysDiff <= 30) return `⚠️ EXPIRES IN ${daysDiff} DAYS`;
                          if (daysDiff <= 90) return `📅 Expires in ${daysDiff} days`;
                          return `✅ Valid for ${daysDiff} days`;
                        })()}
                      </div>
                    </div>
                  )}
                  
                  <div><strong>Insurance Company:</strong> 
                    <span className="font-bold text-blue-600">
                      {insuranceData?.insurance_company || 
                       (insuranceData?.insurance_data_source?.includes("No Insurance on File") ? "No Insurance on File" : "Not Available")}
                    </span>
                  </div>
                  <div><strong>Liability Insurance Expiry:</strong> {
                    insuranceData?.liability_insurance_date ? formatDate(insuranceData.liability_insurance_date) :
                    (insuranceData?.insurance_data_source?.includes("No Insurance on File") ? "No Insurance on File" : "Not Available")
                  }</div>
                  <div><strong>Liability Insurance Amount:</strong> {
                    insuranceData?.liability_insurance_amount ? `$${insuranceData.liability_insurance_amount.toLocaleString()}` :
                    (insuranceData?.insurance_data_source?.includes("No Insurance on File") ? "No Insurance on File" : "Not Available")
                  }</div>
                  <div><strong>Cargo Insurance Date:</strong> {formatDate(carrierData.cargo_insurance_date)}</div>
                  <div><strong>Cargo Insurance Amount:</strong> {carrierData.cargo_insurance_amount ? `$${carrierData.cargo_insurance_amount.toLocaleString()}` : 'N/A'}</div>
                  <div><strong>Bond Insurance Date:</strong> {formatDate(carrierData.bond_insurance_date)}</div>
                  <div><strong>Bond Insurance Amount:</strong> {carrierData.bond_insurance_amount ? `$${carrierData.bond_insurance_amount.toLocaleString()}` : 'N/A'}</div>
                  
                  {insuranceData?.insurance_data_source && (
                    <div className="mt-3 pt-3 border-t border-gray-300">
                      <div className="text-xs text-gray-600">
                        <strong>Data Source:</strong> {insuranceData.insurance_data_source}
                        {insuranceData.cached_at && ' (Cached)'}
                      </div>
                    </div>
                  )}
                  
                  <div className="font-semibold text-gray-700 mt-3">Classifications:</div>
                  <div className="whitespace-pre-wrap break-words">
                    {displayValue(carrierData.classdef)}
                  </div>
                </div>
                )}
              </div>
              
              {/* Add Inspection Data Section */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                  <Clipboard className="w-5 h-5 text-blue-600" />
                  Inspection History
                </h3>
                <div className="space-y-2 text-sm">
                  <div><strong>Last Inspection Date:</strong> {formatDate(carrier.last_inspection_date)}</div>
                  <div><strong>Total Inspections:</strong> {displayValue(carrier.total_inspections)}</div>
                  <div><strong>Total Violations:</strong> 
                    <span className={`ml-2 ${
                      carrier.total_violations > 0 ? 'text-red-600 font-bold' : 'text-green-600'
                    }`}>
                      {displayValue(carrier.total_violations)}
                    </span>
                  </div>
                  <div><strong>Out of Service Violations:</strong> 
                    <span className={`ml-2 ${
                      carrier.out_of_service_violations > 0 ? 'text-red-600 font-bold' : 'text-green-600'
                    }`}>
                      {displayValue(carrier.out_of_service_violations)}
                    </span>
                  </div>
                  <div><strong>Violation Rate:</strong> 
                    <span className={`ml-2 px-2 py-1 rounded text-xs ${
                      carrier.violation_rate < 0.2 ? 'bg-green-100 text-green-800' :
                      carrier.violation_rate < 0.4 ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {carrier.violation_rate ? `${(carrier.violation_rate * 100).toFixed(1)}%` : 'N/A'}
                    </span>
                  </div>
                  
                  {carrier.sample_vin && (
                    <div className="mt-3">
                      <div className="font-semibold text-gray-700">Vehicle Information:</div>
                      <div><strong>Sample VIN:</strong> <code className="bg-gray-200 px-1 rounded text-xs">{carrier.sample_vin}</code></div>
                      <div><strong>Total Vehicles:</strong> {displayValue(carrier.total_vehicles)}</div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'business' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                  <Building className="w-5 h-5 text-blue-600" />
                  Business Structure
                </h3>
                <div className="space-y-2 text-sm">
                  <div><strong>Business Organization:</strong> {displayValue(carrier.business_org_desc)}</div>
                  <div><strong>Business Org ID:</strong> {displayValue(carrier.business_org_id)}</div>
                  <div><strong>Carrier/Shipper:</strong> {displayValue(carrier.carship)}</div>
                  <div><strong>Entity Type:</strong> {displayValue(carrier.entity_type)}</div>
                  
                  <div className="font-semibold text-gray-700 mt-3">Company Officers:</div>
                  <div><strong>Officer 1:</strong> {displayValue(carrier.company_officer_1)}</div>
                  <div><strong>Officer 2:</strong> {displayValue(carrier.company_officer_2)}</div>
                  
                  <div className="font-semibold text-gray-700 mt-3">Registration Info:</div>
                  <div><strong>Add Date:</strong> {formatDate(carrier.add_date)}</div>
                  <div><strong>Status Code:</strong> {displayValue(carrier.status_code)}</div>
                  <div><strong>Point Number:</strong> {displayValue(carrier.pointnum)}</div>
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                  <Globe className="w-5 h-5 text-blue-600" />
                  Operating Territory
                </h3>
                <div className="space-y-2 text-sm">
                  <div className="font-semibold text-gray-700">Interstate Operations:</div>
                  <div><strong>Beyond 100 miles:</strong> {carrier.interstate_beyond_100_miles === '1' ? '✅ Yes' : '❌ No'}</div>
                  <div><strong>Within 100 miles:</strong> {carrier.interstate_within_100_miles === '1' ? '✅ Yes' : '❌ No'}</div>
                  
                  <div className="font-semibold text-gray-700 mt-3">Intrastate Operations:</div>
                  <div><strong>Beyond 100 miles:</strong> {carrier.intrastate_beyond_100_miles === '1' ? '✅ Yes' : '❌ No'}</div>
                  <div><strong>Within 100 miles:</strong> {carrier.intrastate_within_100_miles === '1' ? '✅ Yes' : '❌ No'}</div>
                  
                  <div className="font-semibold text-gray-700 mt-3">Regional Information:</div>
                  <div><strong>OMC Region:</strong> {displayValue(carrier.phy_omc_region)}</div>
                  <div><strong>Fleet Size Category:</strong> {displayValue(carrier.fleetsize)}</div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'cargo' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                  <Package className="w-5 h-5 text-blue-600" />
                  Cargo Types
                </h3>
                <div className="space-y-2 text-sm">
                  <div className="font-semibold text-gray-700">Primary Cargo:</div>
                  <div className="whitespace-pre-wrap break-words">
                    {displayValue(carrier.cargo_carried)}
                  </div>
                  
                  <div className="font-semibold text-gray-700 mt-3">Specific Cargo Types:</div>
                  {carrier.crgo_genfreight === 'X' && <div>✅ General Freight</div>}
                  {carrier.crgo_household === 'X' && <div>✅ Household Goods</div>}
                  {carrier.crgo_bldgmat === 'X' && <div>✅ Building Materials</div>}
                  {carrier.crgo_chem === 'X' && <div>✅ Chemicals</div>}
                  {carrier.crgo_drivetow === 'X' && <div>✅ Drive/Tow Away</div>}
                  {carrier.crgo_beverages === 'X' && <div>✅ Beverages</div>}
                  {carrier.crgo_coldfood === 'X' && <div>✅ Refrigerated Food</div>}
                  {carrier.crgo_drybulk === 'X' && <div>✅ Dry Bulk</div>}
                  {carrier.crgo_farmsupp === 'X' && <div>✅ Farm Supplies</div>}
                  {carrier.crgo_garbage === 'X' && <div>✅ Garbage/Refuse</div>}
                  {carrier.crgo_grainfeed === 'X' && <div>✅ Grain/Feed</div>}
                  {carrier.crgo_coalcoke === 'X' && <div>✅ Coal/Coke</div>}
                  {carrier.crgo_construct === 'X' && <div>✅ Construction</div>}
                  {carrier.crgo_intermodal === 'X' && <div>✅ Intermodal</div>}
                  {carrier.crgo_cargoothr === 'X' && <div>✅ Other: {displayValue(carrier.crgo_cargoothr_desc)}</div>}
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                  <Activity className="w-5 h-5 text-blue-600" />
                  Operations Details
                </h3>
                <div className="space-y-2 text-sm">
                  <div><strong>Carrier Operation:</strong> {displayValue(carrier.carrier_operation)}</div>
                  <div><strong>Classification:</strong></div>
                  <div className="whitespace-pre-wrap break-words text-xs bg-white p-2 rounded">
                    {displayValue(carrier.classdef)}
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'contact' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                  <MapPin className="w-5 h-5 text-blue-600" />
                  Physical Location
                </h3>
                <div className="space-y-2 text-sm">
                  <div><strong>Street:</strong> {displayValue(carrier.physical_address || carrier.phy_street)}</div>
                  <div><strong>City:</strong> {displayValue(carrier.physical_city || carrier.phy_city)}</div>
                  <div><strong>State:</strong> {displayValue(carrier.physical_state || carrier.phy_state)}</div>
                  <div><strong>ZIP:</strong> {displayValue(carrier.physical_zip || carrier.phy_zip)}</div>
                  <div><strong>County:</strong> {displayValue(carrier.phy_cnty)}</div>
                  <div><strong>Country:</strong> {displayValue(carrier.phy_country)}</div>
                  <div><strong>Nationality Indicator:</strong> {displayValue(carrier.phy_nationality_indicator)}</div>
                  <div><strong>Undeliverable Physical:</strong> {displayValue(carrier.undeliv_phy)}</div>
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                  <Mail className="w-5 h-5 text-blue-600" />
                  Mailing Address & Contact
                </h3>
                <div className="space-y-2 text-sm">
                  <div><strong>Mailing Street:</strong> {displayValue(carrier.carrier_mailing_street)}</div>
                  <div><strong>Mailing City:</strong> {displayValue(carrier.carrier_mailing_city)}</div>
                  <div><strong>Mailing State:</strong> {displayValue(carrier.carrier_mailing_state)}</div>
                  <div><strong>Mailing ZIP:</strong> {displayValue(carrier.carrier_mailing_zip)}</div>
                  <div><strong>Mailing County:</strong> {displayValue(carrier.carrier_mailing_cnty)}</div>
                  <div><strong>Mailing Country:</strong> {displayValue(carrier.carrier_mailing_country)}</div>
                  <div><strong>Mail Nationality:</strong> {displayValue(carrier.mail_nationality_indicator)}</div>
                  <div><strong>Mailing Undeliverable Date:</strong> {formatDate(carrier.carrier_mailing_und_date)}</div>
                  
                  <div className="font-semibold text-gray-700 mt-3">Contact Information:</div>
                  <div><strong>Phone:</strong> {displayValue(carrier.phone || carrier.telephone)}</div>
                  <div><strong>Cell Phone:</strong> {displayValue(carrier.cell_phone)}</div>
                  <div><strong>Fax:</strong> {displayValue(carrier.fax)}</div>
                  <div><strong>Email:</strong> {displayValue(carrier.email_address || carrier.email)}</div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'raw' && (
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="text-lg font-semibold mb-3">All Available Data Fields</h3>
              <div className="text-xs">
                <table className="w-full">
                  <thead>
                    <tr className="bg-gray-200">
                      <th className="text-left p-2 font-semibold">Field Name</th>
                      <th className="text-left p-2 font-semibold">Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    {allFields.map((field, index) => (
                      <tr key={field} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                        <td className="p-2 font-mono text-blue-700">{field}</td>
                        <td className="p-2 break-all">{displayValue(carrier[field])}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="mt-4 text-sm text-gray-600">
                Total fields: {allFields.length}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="bg-gray-100 px-6 py-3 rounded-b-lg flex justify-between items-center">
          <div className="text-sm text-gray-600">
            Last Updated: {formatDate(carrier.mcs150_date || carrier.updated_at)}
          </div>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default ComprehensiveCarrierProfile;