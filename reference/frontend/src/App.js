// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import { Route, Routes, Navigate } from "react-router-dom";
import Sessions from './pages/Sessions';
import SessionDetails from './pages/SessionDetails';
import Images from './pages/Images';
import Stages from "./pages/Stages";
import Instances from "./pages/Instances";
import CreateSession from "./pages/CreateSession";
import AuthProvider from './components/AuthProvider';
import './App.css';

function App() {
  
  return (
    <AuthProvider>
      <div className="App">
        <Routes>
          <Route path="/sessions" element={<Sessions/>} />
          <Route path="/images" element={<Images/>} />
          <Route path="/instances" element={<Instances/>} />
          <Route path="/stages" element={<Stages/>} />
          <Route path="/createSession" element={<CreateSession/>} />
          <Route path="/sessions/:sessionId" element={<SessionDetails />} />
          <Route path="*" element={<Navigate to="/sessions" />} />
        </Routes>
      </div>
    </AuthProvider>
  );
}

export default App;
