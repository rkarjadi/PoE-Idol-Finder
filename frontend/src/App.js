import React, { useState, useEffect } from 'react';

const App = () => {
  
  useEffect(() => {
    window.location.href = 'http://localhost:5000/authorize';
  })

  return (
    <div>
      Redirecting to Authorization Page
    </div>
  );
};

export default App;

// Redirect works, but after authorization it redirects to backend, not front end.