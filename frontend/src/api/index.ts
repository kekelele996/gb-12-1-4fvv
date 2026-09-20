import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/auth/token/refresh/`, {
            refresh: refreshToken,
          });
          
          localStorage.setItem('access_token', response.data.access);
          originalRequest.headers.Authorization = `Bearer ${response.data.access}`;
          
          return api(originalRequest);
        } catch (refreshError) {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('user');
          window.location.href = '/login';
        }
      }
    }
    
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (data: { username: string; password: string }) =>
    api.post('/auth/login/', data),
  register: (data: any) => api.post('/auth/register/', data),
  getCurrentUser: () => api.get('/auth/me/'),
  updateCurrentUser: (data: any) => api.put('/auth/me/', data),
  getStudentProfile: () => api.get('/auth/profile/student/'),
  updateStudentProfile: (data: any) => api.put('/auth/profile/student/', data),
  getConsultantProfile: () => api.get('/auth/profile/consultant/'),
  updateConsultantProfile: (data: any) => api.put('/auth/profile/consultant/', data),
  getConsultants: () => api.get('/auth/consultants/'),
};

export const universityAPI = {
  getUniversities: (params?: any) => api.get('/universities/universities/', { params }),
  getUniversity: (id: number) => api.get(`/universities/universities/${id}/`),
  getPrograms: (params?: any) => api.get('/universities/programs/', { params }),
  getProgram: (id: number) => api.get(`/universities/programs/${id}/`),
  getRecommendations: (params?: any) => api.get('/universities/recommendations/', { params }),
  createRecommendation: (data: any) => api.post('/universities/recommendations/', data),
  markRecommendationViewed: (id: number) => api.post(`/universities/recommendations/${id}/mark_viewed/`),
};

export const applicationAPI = {
  getApplications: (params?: any) => api.get('/applications/projects/', { params }),
  getApplication: (id: number) => api.get(`/applications/projects/${id}/`),
  createApplication: (data: any) => api.post('/applications/projects/', data),
  updateApplication: (id: number, data: any) => api.put(`/applications/projects/${id}/`, data),
  deleteApplication: (id: number) => api.delete(`/applications/projects/${id}/`),
  changeStatus: (id: number, data: { status: string; reason?: string }) =>
    api.post(`/applications/projects/${id}/change_status/`, data),
  getStatusHistory: (id: number) => api.get(`/applications/projects/${id}/status_history/`),
};

export const documentAPI = {
  getDocuments: (params?: any) => api.get('/documents/documents/', { params }),
  getDocument: (id: number) => api.get(`/documents/documents/${id}/`),
  createDocument: (data: any) => api.post('/documents/documents/', data),
  updateDocument: (id: number, data: any) => api.put(`/documents/documents/${id}/`, data),
  deleteDocument: (id: number) => api.delete(`/documents/documents/${id}/`),
  
  getVersions: (params?: any) => api.get('/documents/versions/', { params }),
  getVersion: (id: number) => api.get(`/documents/versions/${id}/`),
  createVersion: (data: any) => api.post('/documents/versions/', data),
  compareVersions: (id: number, compareWith: number) =>
    api.get(`/documents/versions/${id}/compare/?compare_with=${compareWith}`),
  
  getComments: (params?: any) => api.get('/documents/comments/', { params }),
  createComment: (data: any) => api.post('/documents/comments/', data),
  resolveComment: (id: number) => api.post(`/documents/comments/${id}/resolve/`),
};

export const materialAPI = {
  getMaterials: (params?: any) => api.get('/materials/items/', { params }),
  getMaterial: (id: number) => api.get(`/materials/items/${id}/`),
  createMaterial: (data: any) => api.post('/materials/items/', data),
  updateMaterial: (id: number, data: any) => api.put(`/materials/items/${id}/`, data),
  deleteMaterial: (id: number) => api.delete(`/materials/items/${id}/`),
  markComplete: (id: number) => api.post(`/materials/items/${id}/mark_complete/`),
  markIncomplete: (id: number) => api.post(`/materials/items/${id}/mark_incomplete/`),
  getTemplates: (params?: any) => api.get('/materials/templates/', { params }),
};

export const timelineAPI = {
  getEvents: (params?: any) => api.get('/timelines/events/', { params }),
  getEvent: (id: number) => api.get(`/timelines/events/${id}/`),
  createEvent: (data: any) => api.post('/timelines/events/', data),
  updateEvent: (id: number, data: any) => api.put(`/timelines/events/${id}/`, data),
  deleteEvent: (id: number) => api.delete(`/timelines/events/${id}/`),
  markComplete: (id: number) => api.post(`/timelines/events/${id}/mark_complete/`),
  markIncomplete: (id: number) => api.post(`/timelines/events/${id}/mark_incomplete/`),
  getUpcoming: (days?: number) => api.get(`/timelines/events/upcoming/?days=${days || 7}`),
  
  getNotifications: (params?: any) => api.get('/timelines/notifications/', { params }),
  getUnreadNotifications: () => api.get('/timelines/notifications/unread/'),
  markNotificationRead: (id: number) => api.post(`/timelines/notifications/${id}/mark_read/`),
  markAllNotificationsRead: () => api.post('/timelines/notifications/mark_all_read/'),
};

export const messageAPI = {
  getConversations: (params?: any) => api.get('/messages/conversations/', { params }),
  getConversation: (id: number) => api.get(`/messages/conversations/${id}/`),
  createConversation: (data: any) => api.post('/messages/conversations/', data),
  sendMessage: (conversationId: number, data: any) =>
    api.post(`/messages/conversations/${conversationId}/send_message/`, data),
  markConversationRead: (id: number) => api.post(`/messages/conversations/${id}/mark_read/`),
  
  getMessages: (params?: any) => api.get('/messages/messages/', { params }),
};

export const analyticsAPI = {
  getApplicationDashboard: () => api.get('/analytics/dashboard/applications/'),
  getConsultantDashboard: () => api.get('/analytics/dashboard/consultant/'),
  getAdminDashboard: () => api.get('/analytics/dashboard/admin/'),
};

export default api;
