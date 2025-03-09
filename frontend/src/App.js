import React, { useState, useEffect } from 'react';

const App = () => {
  const [isAuthorized, setIsAuthorized] = useState(false);
  const [stashes, setStashes] = useState([]);
  const [selectedStash, setSelectedStash] = useState('');
  const [stashesFetched, setStashesFetched] = useState(false);
  
  useEffect(() => {
    const checkAuthorization = async () => {
      const response = await fetch("/is_authorized");
      const data = await response.json();

      if (data.authorized) {
        setIsAuthorized(true);
        localStorage.setItem("isAuthorized", true);
      } else {
        localStorage.removeItem("isAuthorized");
        window.location.href = 'http://localhost:5000/authorize';
      }
    };

    // const authorized = localStorage.getItem("isAuthorized");
    if (isAuthorized) {
      // setIsAuthorized(true);
      console.log("You are authorized.")
    } else {
      checkAuthorization();
    }

  }, []);

  const fetchStashes = async () => {
    const response = await fetch("/get_stashes");
    const data = await response.json();
    setStashes(data);
    setStashesFetched(true);
  };

  const handleStashChange = (event) => {
    setSelectedStash(event.target.value);
  };

  if (!isAuthorized) {
    return (
      <div>
        Redirecting to Authorization Page
      </div>
    );
  }

  return (
    <div>
      <h1>Authorized</h1>
      <h2>Stashes</h2>
      <button onClick={fetchStashes}>Fetch Stashes</button>
      {stashesFetched && (
        <select value={selectedStash} onChange={handleStashChange}>
          <option value="">Select a stash</option>
          {stashes.map((stash, index) => (
            <option key={index} value={stash.id}>
              {stash.name}
            </option>
          ))}
        </select>
      )}
      {selectedStash && (
        <div>
          <h3>Selected Stash ID: {selectedStash}</h3>
        </div>
      )}
    </div>
  );
};

export default App;
