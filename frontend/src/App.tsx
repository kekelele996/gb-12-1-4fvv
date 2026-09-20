import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, Spin } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { useAuthStore } from './store/useAuthStore';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Universities from './pages/Universities';
import Applications from './pages/Applications';
import Documents from './pages/Documents';
import Timeline from './pages/Timeline';
import Messages from './pages/Messages';
import Profile from './pages/Profile';

const PrivateRoute: React.FC<{ element: React.ReactElement }> = ({ element }) => {
  const { isAuthenticated, isLoading } = useAuthStore();
  
  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Spin size="large" />
      </div>
    );
  }
  
  return isAuthenticated ? element : <Navigate to="/login" replace />;
};

const PublicRoute: React.FC<{ element: React.ReactElement }> = ({ element }) => {
  const { isAuthenticated } = useAuthStore();
  return !isAuthenticated ? element : <Navigate to="/dashboard" replace />;
};

const App: React.FC = () => {
  const { isLoading } = useAuthStore();

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <ConfigProvider locale={zhCN}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<PublicRoute element={<Login />} />} />
          <Route path="/register" element={<PublicRoute element={<Login />} />} />
          
          <Route
            path="/"
            element={
              <PrivateRoute
                element={
                  <Layout>
                    <Navigate to="/dashboard" replace />
                  </Layout>
                }
              />
            }
          />
          <Route
            path="/dashboard"
            element={
              <PrivateRoute
                element={
                  <Layout>
                    <Dashboard />
                  </Layout>
                }
              />
            }
          />
          <Route
            path="/universities"
            element={
              <PrivateRoute
                element={
                  <Layout>
                    <Universities />
                  </Layout>
                }
              />
            }
          />
          <Route
            path="/applications"
            element={
              <PrivateRoute
                element={
                  <Layout>
                    <Applications />
                  </Layout>
                }
              />
            }
          />
          <Route
            path="/documents"
            element={
              <PrivateRoute
                element={
                  <Layout>
                    <Documents />
                  </Layout>
                }
              />
            }
          />
          <Route
            path="/timeline"
            element={
              <PrivateRoute
                element={
                  <Layout>
                    <Timeline />
                  </Layout>
                }
              />
            }
          />
          <Route
            path="/messages"
            element={
              <PrivateRoute
                element={
                  <Layout>
                    <Messages />
                  </Layout>
                }
              />
            }
          />
          <Route
            path="/profile"
            element={
              <PrivateRoute
                element={
                  <Layout>
                    <Profile />
                  </Layout>
                }
              />
            }
          />
          
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
};

export default App;
