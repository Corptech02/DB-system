import React, { useState, useEffect } from 'react';
import { X, Phone, Mail, MapPin, Truck, Users, Shield, Calendar, Building, AlertTriangle, CheckCircle, Loader2 } from 'lucide-react';
import { format } from 'date-fns';
import { Carrier } from '../types';

interface CarrierProfileProps {
  carrier: Carrier;
  onClose: () => void;
}

const CarrierProfile: React.FC<CarrierProfileProps> = ({ carrier, onClose }) => {
  const [carrierData, setCarrierData] = useState<Carrier>(carrier);
  const [insuranceData, setInsuranceData] = useState<any>(null);
  const [isLoadingInsurance, setIsLoadingInsurance] = useState(true);
  const [insuranceFetchFailed, setInsuranceFetchFailed] = useState(false);

  useEffect(() => {
    // Immediately show loading state for insurance only
    setIsLoadingInsurance(true);
    setInsuranceFetchFailed(false);
    
    // Fetch fresh carrier data with insurance info
    const fetchCarrierDetails = async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/carriers/${carrier.usdot_number}`);
        if (response.ok) {
          const data = await response.json();
          // Update carrier data
          setCarrierData(data);
          
          // Check if insurance data was actually fetched
          if (data.insurance_data_source === "Error" || data.insurance_data_source === "Not Available") {
            setInsuranceFetchFailed(true);
          } else {
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
        setIsLoadingInsurance(false);
      }
    };

    fetchCarrierDetails();
  }, [carrier.usdot_number]);
  const getInsuranceStatus = (date: string | undefined) => {
    if (!date) return { status: 'Unknown', color: 'gray', icon: AlertTriangle };
    
    const insuranceDate = new Date(date);
    const today = new Date();
    const daysDiff = Math.floor((insuranceDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
    
    if (daysDiff < 0) return { status: 'Expired', color: 'danger', icon: AlertTriangle };
    if (daysDiff <= 30) return { status: 'Expiring Soon', color: 'warning', icon: AlertTriangle };
    if (daysDiff <= 90) return { status: 'Expiring', color: 'yellow', icon: AlertTriangle };
    return { status: 'Valid', color: 'success', icon: CheckCircle };
  };

  const insuranceStatus = getInsuranceStatus(insuranceData?.liability_insurance_date);

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-primary-600 text-white px-6 py-4">
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-2xl font-bold">{carrierData.legal_name}</h2>
              {carrierData.dba_name && (
                <p className="text-primary-100 mt-1">DBA: {carrierData.dba_name}</p>
              )}
              <p className="text-primary-200 mt-2">USDOT #{carrierData.usdot_number}</p>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:text-primary-100 transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="overflow-y-auto max-h-[calc(90vh-120px)] p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            {/* Basic Information */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 border-b pb-2">Basic Information</h3>
              
              <div className="space-y-3">
                <div className="flex items-start">
                  <Building className="w-5 h-5 text-gray-400 mr-3 mt-0.5" />
                  <div>
                    <p className="text-sm text-gray-600">Entity Type</p>
                    <p className="font-medium">{carrierData.entity_type || 'N/A'}</p>
                  </div>
                </div>

                <div className="flex items-start">
                  <MapPin className="w-5 h-5 text-gray-400 mr-3 mt-0.5" />
                  <div>
                    <p className="text-sm text-gray-600">Address</p>
                    <p className="font-medium">
                      {carrierData.physical_address && `${carrierData.physical_address}, `}
                      {carrierData.physical_city}, {carrierData.physical_state} {carrierData.physical_zip}
                    </p>
                  </div>
                </div>

                {carrierData.telephone && (
                  <div className="flex items-start">
                    <Phone className="w-5 h-5 text-gray-400 mr-3 mt-0.5" />
                    <div>
                      <p className="text-sm text-gray-600">Phone</p>
                      <p className="font-medium">{carrierData.telephone}</p>
                    </div>
                  </div>
                )}

                {carrierData.email && (
                  <div className="flex items-start">
                    <Mail className="w-5 h-5 text-gray-400 mr-3 mt-0.5" />
                    <div>
                      <p className="text-sm text-gray-600">Email</p>
                      <p className="font-medium">{carrierData.email}</p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Operating Information */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 border-b pb-2">Operating Information</h3>
              
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm text-gray-600">Operating Status</span>
                  <span className={`badge ${
                    carrierData.operating_status === 'ACTIVE' ? 'badge-success' :
                    carrierData.operating_status === 'INACTIVE' ? 'bg-gray-100 text-gray-700' :
                    'badge-danger'
                  }`}>
                    {carrierData.operating_status}
                  </span>
                </div>

                <div className="flex items-start">
                  <Truck className="w-5 h-5 text-gray-400 mr-3 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-sm text-gray-600">Fleet Size</p>
                    <div className="grid grid-cols-2 gap-4 mt-1">
                      <div>
                        <p className="font-medium">{carrierData.power_units || 0}</p>
                        <p className="text-xs text-gray-500">Power Units</p>
                      </div>
                      <div>
                        <p className="font-medium">{carrierData.drivers || 0}</p>
                        <p className="text-xs text-gray-500">Drivers</p>
                      </div>
                    </div>
                  </div>
                </div>

                {carrierData.hazmat_flag && (
                  <div className="flex items-center p-3 bg-warning-50 rounded-lg">
                    <Shield className="w-5 h-5 text-warning-600 mr-2" />
                    <span className="text-sm font-medium text-warning-800">Hazmat Certified</span>
                  </div>
                )}
              </div>
            </div>

            {/* Insurance Information */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 border-b pb-2">Insurance Information</h3>
              
              {isLoadingInsurance ? (
                <div className="p-8 rounded-lg border-2 border-primary-200 bg-primary-50 animate-pulse">
                  <div className="flex flex-col items-center justify-center">
                    <Loader2 className="w-8 h-8 text-primary-600 animate-spin mb-3" />
                    <p className="text-primary-700 font-medium">Fetching real-time insurance data...</p>
                    <p className="text-sm text-primary-600 mt-1">Connecting to FMCSA L&I System</p>
                  </div>
                </div>
              ) : insuranceFetchFailed ? (
                <div className="p-4 rounded-lg border-2 border-gray-200 bg-gray-50">
                  <div className="flex items-start">
                    <AlertTriangle className="w-5 h-5 text-gray-400 mr-3 mt-0.5" />
                    <div className="flex-1">
                      <p className="font-semibold text-gray-600">Insurance Information Unavailable</p>
                      <p className="text-sm text-gray-500 mt-1">
                        Unable to retrieve insurance data from FMCSA at this time
                      </p>
                      <p className="text-xs text-gray-400 mt-2">
                        Please try again later or contact FMCSA directly
                      </p>
                    </div>
                  </div>
                </div>
              ) : insuranceData ? (
                <div className={`p-4 rounded-lg border-2 ${
                  insuranceStatus.color === 'success' ? 'bg-success-50 border-success-200' :
                  insuranceStatus.color === 'warning' ? 'bg-warning-50 border-warning-200' :
                  insuranceStatus.color === 'danger' ? 'bg-danger-50 border-danger-200' :
                  'bg-gray-50 border-gray-200'
                }`}>
                  <div className="flex items-start">
                    <insuranceStatus.icon className={`w-5 h-5 mr-3 mt-0.5 ${
                      insuranceStatus.color === 'success' ? 'text-success-600' :
                      insuranceStatus.color === 'warning' ? 'text-warning-600' :
                      insuranceStatus.color === 'danger' ? 'text-danger-600' :
                      'text-gray-600'
                    }`} />
                    <div className="flex-1">
                      <p className="font-semibold">{insuranceStatus.status}</p>
                      {insuranceData.liability_insurance_date ? (
                        <p className="text-sm text-gray-600 mt-1">
                          Expires: {format(new Date(insuranceData.liability_insurance_date), 'MMMM d, yyyy')}
                        </p>
                      ) : (
                        <p className="text-sm text-gray-500 mt-1">
                          Expiration Date: Not provided
                        </p>
                      )}
                      {insuranceData.liability_insurance_amount ? (
                        <p className="text-sm text-gray-600 mt-1">
                          Coverage: ${insuranceData.liability_insurance_amount.toLocaleString()}
                        </p>
                      ) : null}
                      {insuranceData.insurance_company ? (
                        <p className="text-sm text-gray-600 mt-1">
                          Provider: {insuranceData.insurance_company}
                        </p>
                      ) : null}
                      {insuranceData.insurance_data_source && (
                        <p className="text-xs text-gray-500 mt-2">
                          Source: {insuranceData.insurance_data_source}
                          {insuranceData.cached_at && ' (Cached)'}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="p-4 rounded-lg border-2 border-gray-200 bg-gray-50">
                  <div className="flex items-center justify-center">
                    <p className="text-gray-500">No insurance data available</p>
                  </div>
                </div>
              )}
            </div>

            {/* Safety & Compliance */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 border-b pb-2">Safety & Compliance</h3>
              
              <div className="space-y-3">
                {carrierData.safety_rating && (
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <span className="text-sm text-gray-600">Safety Rating</span>
                    <span className={`badge ${
                      carrierData.safety_rating === 'SATISFACTORY' ? 'badge-success' :
                      carrierData.safety_rating === 'CONDITIONAL' ? 'badge-warning' :
                      carrierData.safety_rating === 'UNSATISFACTORY' ? 'badge-danger' :
                      'bg-gray-100 text-gray-700'
                    }`}>
                      {carrierData.safety_rating}
                    </span>
                  </div>
                )}

                {carrierData.mcs_150_date && (
                  <div className="flex items-start">
                    <Calendar className="w-5 h-5 text-gray-400 mr-3 mt-0.5" />
                    <div>
                      <p className="text-sm text-gray-600">MCS-150 Update</p>
                      <p className="font-medium">
                        {format(new Date(carrierData.mcs_150_date), 'MMMM d, yyyy')}
                      </p>
                    </div>
                  </div>
                )}

                {carrierData.cargo_carried && (
                  <div>
                    <p className="text-sm text-gray-600 mb-2">Cargo Carried</p>
                    <p className="text-sm bg-gray-50 p-3 rounded">{carrierData.cargo_carried}</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Additional Information */}
          {(carrierData.created_at || carrierData.updated_at) && (
            <div className="mt-6 pt-6 border-t">
              <div className="flex justify-between text-xs text-gray-500">
                {carrierData.created_at && (
                  <span>Added: {format(new Date(carrierData.created_at), 'MM/dd/yyyy')}</span>
                )}
                {carrierData.updated_at && (
                  <span>Updated: {format(new Date(carrierData.updated_at), 'MM/dd/yyyy')}</span>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="bg-gray-50 px-6 py-4 border-t flex justify-end">
          <button
            onClick={onClose}
            className="btn btn-secondary"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default CarrierProfile;