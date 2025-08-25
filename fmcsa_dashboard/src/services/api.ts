import axios, { AxiosInstance } from 'axios';
import {
  Carrier,
  SearchFilters,
  SearchResponse,
  ExportRequest,
  ExportResponse,
  Statistics,
  Lead,
} from '../types';

class ApiService {
  private client: AxiosInstance;
  
  constructor() {
    this.client = axios.create({
      baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    // Add API key if configured
    const apiKey = import.meta.env.VITE_API_KEY;
    if (apiKey) {
      this.client.defaults.headers.common['X-API-Key'] = apiKey;
    }
    
    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 429) {
          console.error('Rate limit exceeded');
        }
        return Promise.reject(error);
      }
    );
  }
  
  // Search endpoints
  async searchCarriers(filters: SearchFilters, page = 1, perPage = 20): Promise<SearchResponse> {
    const response = await this.client.post('/search', {
      ...filters,
      page,
      per_page: perPage,
    });
    return response.data;
  }
  
  async getCarrier(usdotNumber: number): Promise<Carrier> {
    const response = await this.client.get(`/carriers/${usdotNumber}`);
    return response.data;
  }
  
  async searchByInsuranceExpiration(days: number, page = 1, perPage = 20): Promise<SearchResponse> {
    const response = await this.client.get('/search/insurance-expiring', {
      params: { days, page, per_page: perPage },
    });
    return response.data;
  }
  
  // Statistics endpoints
  async getStatistics(state?: string): Promise<Statistics> {
    const response = await this.client.get('/stats', {
      params: state ? { state } : undefined,
    });
    return response.data;
  }
  
  async getSummaryStats(): Promise<any> {
    const response = await this.client.get('/stats/summary');
    return response.data;
  }
  
  async getTopStates(limit = 10): Promise<any[]> {
    const response = await this.client.get('/stats/top-states', {
      params: { limit },
    });
    return response.data;
  }
  
  async getInsuranceForecast(days = 90): Promise<any> {
    const response = await this.client.get('/stats/insurance-expiration-forecast', {
      params: { days },
    });
    return response.data;
  }
  
  // Export endpoints
  async createExport(request: ExportRequest): Promise<ExportResponse> {
    const response = await this.client.post('/export', request);
    return response.data;
  }
  
  async downloadExport(fileId: string): Promise<string> {
    const apiKey = import.meta.env.VITE_API_KEY;
    const params = apiKey ? `?api_key=${apiKey}` : '';
    return `/api/export/download/${fileId}${params}`;
  }
  
  async getExportStatus(fileId: string): Promise<any> {
    const response = await this.client.get(`/export/status/${fileId}`);
    return response.data;
  }
  
  // Lead generation endpoints
  async getExpiringInsuranceLeads(
    daysAhead = 90,
    state?: string,
    minPowerUnits?: number,
    limit = 100
  ): Promise<Lead[]> {
    const response = await this.client.get('/leads/expiring-insurance', {
      params: {
        days_ahead: daysAhead,
        state,
        min_power_units: minPowerUnits,
        limit,
      },
    });
    return response.data;
  }
  
  async getExpiredInsuranceLeads(
    maxDaysExpired = 30,
    state?: string,
    limit = 100
  ): Promise<Lead[]> {
    const response = await this.client.get('/leads/expired-insurance', {
      params: {
        max_days_expired: maxDaysExpired,
        state,
        limit,
      },
    });
    return response.data;
  }
  
  async getHighValueLeads(
    minPowerUnits = 10,
    minDrivers = 10,
    daysAhead = 90,
    limit = 100
  ): Promise<Lead[]> {
    const response = await this.client.get('/leads/high-value', {
      params: {
        min_power_units: minPowerUnits,
        min_drivers: minDrivers,
        days_ahead: daysAhead,
        limit,
      },
    });
    return response.data;
  }
  
  // Admin endpoints
  async triggerManualRefresh(): Promise<any> {
    const response = await this.client.post('/admin/refresh');
    return response.data;
  }
  
  async getSchedulerStatus(): Promise<any> {
    const response = await this.client.get('/admin/scheduler-status');
    return response.data;
  }
  
  async refreshStats(): Promise<any> {
    const response = await this.client.post('/stats/refresh');
    return response.data;
  }
}

export default new ApiService();