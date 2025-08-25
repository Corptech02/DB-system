import React, { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { Search, Filter, RotateCcw } from 'lucide-react';
import { SearchFilters } from '../types';
import { useDebounce } from '../hooks/useDebounce';

interface SearchFormProps {
  onSearch: (filters: SearchFilters) => void;
}

const SearchForm: React.FC<SearchFormProps> = ({ onSearch }) => {
  const { register, handleSubmit, reset, watch } = useForm<SearchFilters>();
  const [showAdvanced, setShowAdvanced] = React.useState(false);
  
  // Watch all form values
  const formValues = watch();
  
  // Debounce the form values to avoid too many API calls
  const debouncedValues = useDebounce(formValues, 500);
  
  const onSubmit = (data: SearchFilters) => {
    // Clean up empty values
    const filters = Object.entries(data).reduce((acc, [key, value]) => {
      if (value !== '' && value !== undefined && value !== null) {
        acc[key as keyof SearchFilters] = value;
      }
      return acc;
    }, {} as SearchFilters);
    
    onSearch(filters);
  };
  
  const handleReset = () => {
    reset();
    onSearch({});
  };
  
  // Auto-search when debounced values change
  useEffect(() => {
    const filters = Object.entries(debouncedValues).reduce((acc, [key, value]) => {
      if (value !== '' && value !== undefined && value !== null) {
        acc[key as keyof SearchFilters] = value;
      }
      return acc;
    }, {} as SearchFilters);
    
    console.log('SearchForm - Auto-searching with filters:', filters);
    onSearch(filters);
  }, [debouncedValues]);
  
  const states = [
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY',
  ];
  
  return (
    <div className="card">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {/* Basic Search */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label htmlFor="usdot_number" className="label">
              USDOT Number
            </label>
            <input
              {...register('usdot_number')}
              type="text"
              className="input"
              placeholder="Enter USDOT number"
            />
          </div>
          
          <div>
            <label htmlFor="legal_name" className="label">
              Legal Name
            </label>
            <input
              {...register('legal_name')}
              type="text"
              className="input"
              placeholder="Enter company name"
            />
          </div>
          
          <div>
            <label htmlFor="state" className="label">
              State
            </label>
            <select {...register('state')} className="input">
              <option value="">All States</option>
              {states.map((state) => (
                <option key={state} value={state}>
                  {state}
                </option>
              ))}
            </select>
          </div>
        </div>
        
        {/* Toggle Advanced Filters */}
        <div>
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="text-sm text-primary-600 hover:text-primary-700 flex items-center"
          >
            <Filter className="w-4 h-4 mr-1" />
            {showAdvanced ? 'Hide' : 'Show'} Advanced Filters
          </button>
        </div>
        
        {/* Advanced Filters */}
        {showAdvanced && (
          <div className="space-y-4 pt-4 border-t">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label htmlFor="city" className="label">
                  City
                </label>
                <input
                  {...register('city')}
                  type="text"
                  className="input"
                  placeholder="Enter city"
                />
              </div>
              
              <div>
                <label htmlFor="entity_type" className="label">
                  Entity Type
                </label>
                <select {...register('entity_type')} className="input">
                  <option value="">All Types</option>
                  <option value="CARRIER">Carrier</option>
                  <option value="BROKER">Broker</option>
                  <option value="FREIGHT_FORWARDER">Freight Forwarder</option>
                  <option value="SHIPPER">Shipper</option>
                </select>
              </div>
              
              <div>
                <label htmlFor="operating_status" className="label">
                  Operating Status
                </label>
                <select {...register('operating_status')} className="input">
                  <option value="">All Statuses</option>
                  <option value="ACTIVE">Active</option>
                  <option value="INACTIVE">Inactive</option>
                  <option value="OUT_OF_SERVICE">Out of Service</option>
                </select>
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label htmlFor="min_power_units" className="label">
                  Min Power Units
                </label>
                <input
                  {...register('min_power_units', { valueAsNumber: true })}
                  type="number"
                  className="input"
                  placeholder="0"
                />
              </div>
              
              <div>
                <label htmlFor="max_power_units" className="label">
                  Max Power Units
                </label>
                <input
                  {...register('max_power_units', { valueAsNumber: true })}
                  type="number"
                  className="input"
                  placeholder="999999"
                />
              </div>
              
              <div>
                <label htmlFor="min_drivers" className="label">
                  Min Drivers
                </label>
                <input
                  {...register('min_drivers', { valueAsNumber: true })}
                  type="number"
                  className="input"
                  placeholder="0"
                />
              </div>
              
              <div>
                <label htmlFor="max_drivers" className="label">
                  Max Drivers
                </label>
                <input
                  {...register('max_drivers', { valueAsNumber: true })}
                  type="number"
                  className="input"
                  placeholder="999999"
                />
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label htmlFor="safety_rating" className="label">
                  Safety Rating
                </label>
                <select {...register('safety_rating')} className="input">
                  <option value="">All Ratings</option>
                  <option value="SATISFACTORY">Satisfactory</option>
                  <option value="CONDITIONAL">Conditional</option>
                  <option value="UNSATISFACTORY">Unsatisfactory</option>
                </select>
              </div>
              
              <div>
                <label htmlFor="insurance_expiring_days" className="label">
                  Insurance Expiring (Days)
                </label>
                <input
                  {...register('insurance_expiring_days', { valueAsNumber: true })}
                  type="number"
                  className="input"
                  placeholder="30, 60, 90"
                />
              </div>
              
              <div className="flex items-end">
                <label className="flex items-center">
                  <input
                    {...register('hazmat_only')}
                    type="checkbox"
                    className="rounded border-gray-300 text-primary-600 shadow-sm focus:border-primary-500 focus:ring focus:ring-primary-200 focus:ring-opacity-50"
                  />
                  <span className="ml-2 text-sm text-gray-700">Hazmat Only</span>
                </label>
              </div>
            </div>
          </div>
        )}
        
        {/* Action Buttons */}
        <div className="flex justify-end space-x-3">
          <button
            type="button"
            onClick={handleReset}
            className="btn btn-secondary"
          >
            <RotateCcw className="w-4 h-4 mr-2" />
            Reset
          </button>
          <button type="submit" className="btn btn-primary">
            <Search className="w-4 h-4 mr-2" />
            Search
          </button>
        </div>
      </form>
    </div>
  );
};

export default SearchForm;