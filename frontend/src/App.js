import React, { useState, useEffect } from 'react';

function App() {
  const [dnsRecords, setDnsRecords] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/dns_records')  // Assuming Flask backend running on same server
      .then(response => response.json())
      .then(data => {
        setDnsRecords(data);
        setLoading(false);
      });
  }, []);

  return (
    <div>
      <h1>DNS Records</h1>
      {loading ? (
        <p>Loading...</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>IP</th>
            </tr>
          </thead>
          <tbody>
            {dnsRecords.map((record, index) => (
              <tr key={index}>
                <td>{record.name}</td>
                <td>{record.type}</td>
                <td>{record.ip || record.point_to}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default App;
