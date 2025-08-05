import React from 'react';
import ReactDOM from 'react-dom/client';
import SimpleApp from './SimpleApp.tsx';
import './index.css';

// 确保在开发环境中启用React严格模式
const StrictModeWrapper = import.meta.env.DEV ? React.StrictMode : React.Fragment;

ReactDOM.createRoot(document.getElementById('root')!).render(
  <StrictModeWrapper>
    <SimpleApp />
  </StrictModeWrapper>
);