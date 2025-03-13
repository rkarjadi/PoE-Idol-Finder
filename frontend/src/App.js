import React, { useState, useEffect } from 'react';
import './App.css'; // Import the CSS file

const App = () => {
  // const [isAuthorized, setIsAuthorized] = useState(false);
  const [stashes, setStashes] = useState([]);
  const [selectedStash, setSelectedStash] = useState('');
  const [stashesFetched, setStashesFetched] = useState(false);
  const [stashIdols, setStashIdols] = useState([]);
  const [contentTags, setContentTags] = useState([]);
  const [selectedContentTag, setSelectedContentTag] = useState('');
  
  useEffect(() => {
    // const checkAuthorization = async () => {
    //   const response = await fetch("https://poe-idol-finder.onrender.com/is_authorized");
    //   const data = await response.json();

    //   if (data.authorized) {
    //     setIsAuthorized(true);
    //     localStorage.setItem("isAuthorized", true);
    //   } else {
    //     localStorage.removeItem("isAuthorized");
    //     window.location.href = 'https://poe-idol-finder.onrender.com/authorize';
    //   }
    // };

    // if (isAuthorized) {
    //   console.log("You are authorized.")
    // } else {
    //   checkAuthorization();
    // }
    window.location.href = 'https://poe-idol-finder.onrender.com/is_authorized'
    const handleBeforeUnload = () => {
      navigator.sendBeacon('/logout');
    };

    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };

  }, []);

  // Retrieves all stashes (names and ids)
  const fetchStashes = async () => {
    const response = await fetch("https://poe-idol-finder.onrender.com/get_stashes");
    const data = await response.json();
    setStashes(data);
    setStashesFetched(true);
  };

  const fetchStashIdols = async (stashId) => {
    const response = await fetch(`https://poe-idol-finder.onrender.com/get_idols_with_content_tags/${stashId}`);
    const data = await response.json()
    setStashIdols(data);

    // Gets the content tags existing in the idols (ie. only ones that exist in the set)
    const tags = new Set();
    data.forEach(item => {
      Object.keys(item.contentTags).forEach(tag => tags.add(tag));
    });
    setContentTags(Array.from(tags));
  }

  // Handles change when stash is selected
  const handleStashChange = (event) => {
    const stashId = event.target.value;
    setSelectedStash(stashId);
    fetchStashIdols(stashId);
  };

  // Handles content tag change on dropdown bar
  const handleContentTagChange = (event) => {
    setSelectedContentTag(event.target.value);
  };

  // Filters the idols to the select content tag and sorts
  const filteredIdols = selectedContentTag
    ? stashIdols
        .filter(item => item.contentTags[selectedContentTag])
        .sort((a, b) => b.contentTags[selectedContentTag] - a.contentTags[selectedContentTag])
    : stashIdols;

  // if (!isAuthorized) {
  //   return (
  //     <div>
  //       Redirecting to Authorization Page
  //     </div>
  //   );
  // }

  return (
    <div className="center">
      <h1>PoE Phrecia Idol Finder</h1>
      <div className="controls">
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
          <>
            <label htmlFor="contentTagSelect">Filter by Content:</label>
            <select id="contentTagSelect" value={selectedContentTag} onChange={handleContentTagChange}>
              <option value="">All</option>
              {contentTags.map((tag, index) => (
                <option key={index} value={tag}>
                  {tag}
                </option>
              ))}
            </select>
          </>
        )}
      </div>
      {selectedStash && (
        <div className="stash-contents">
          {filteredIdols.length === 0 ? (
            <p>No idols found in Stash</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Icon</th>
                  <th>Name</th>
                  <th>Base Type</th>
                  <th>Mods</th>
                  <th>Content Tags</th>
                </tr>
              </thead>
              <tbody>
                {filteredIdols.map((item, index) => (
                  <tr key={index}>
                    <td><img src={item.icon} alt={item.name || item.typeLine} /></td>
                    <td>{item.name || item.typeLine}</td>
                    <td>{item.baseType}</td>
                    <td>
                      <ul>
                        {item.explicitMods.map((mod, modIndex) => (
                          <li key={modIndex}>{mod}</li>
                        ))}
                      </ul>
                    </td>
                    <td>
                      <ul>
                        {Object.entries(item.contentTags).map(([key, value], tagIndex) => (
                          <li key={tagIndex}>{key}: {value}</li>
                        ))}
                      </ul>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
};

export default App;
