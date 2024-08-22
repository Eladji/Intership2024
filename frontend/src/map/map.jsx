import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import axios from 'axios';
import 'leaflet/dist/leaflet.css';
import './map.css';
// Define custom icons for relay points and drivers
const relayIcon = L.icon({
  iconUrl: '../assets/46087.png', // Path to the icon
  iconSize: [32, 32], // Size of the icon
  iconAnchor: [16, 32], // Anchor point of the icon
});

const driverIcon = L.icon({
  iconUrl: '../assets/fast-delivery-truck.svg',
  iconSize: [32, 32],
  iconAnchor: [16, 32],
});

const MyMap = () => {
  const [relayPoints, setRelayPoints] = useState([]);
  const [drivers, setDrivers] = useState([]);
  const [error, setError] = useState(null);
  useEffect(() => {
    const fetchPositions = async () => {
      try {
        // Replace these URLs with your actual API endpoints
        const relayResponse = await axios.get('127.0.0.1:5000/relay-points');
        setRelayPoints(relayResponse.data);

        const driverResponse = await axios.get('127.0.0.1:5000/drivers');
        setDrivers(driverResponse.data); 
      } catch (error) {
        console.error('Error fetching positions:', error);
        setError('Sorry, can\'t load the map');
      } //api not set up yet for the driver the app need to be finish first
    };

    // Fetch positions on component mount and set intervals for updates
    fetchPositions();
    const interval = setInterval(fetchPositions, 5000); // Update every 5 seconds

    return () => clearInterval(interval); // Cleanup on component unmount
  }, []);
  if (error) {
    return <div>{error}</div>;
  }

  return (
    <div>

    <MapContainer center={[46.603354, 1.888334]} zoom={13} style={{ height: "100vh", width: "100%" }}>
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
      {Array.isArray(relayPoints) && relayPoints.length > 0 ? (
        relayPoints.map((point, index) => (
          <Marker
          key={`relay-${index}`}
          position={[point.position]}
          icon={relayIcon}
          >
      <Popup>Relay Point {index + 1}</Popup>
    </Marker>
  ))
) : (
  <div className="no-relay-points">
            No relay points available
          </div>
)}
      {Array.isArray(drivers) && drivers.length > 0 ? (
        drivers.map((drivers, index) => (
         <Marker
        key={`driver-${index}`}
        position={[driver.latitude, driver.longitude]}
        icon={driverIcon}
        >
          <Popup>Driver {index + 1}</Popup>
        </Marker>
     ))
    ):(
        <div className="no-drivers">
          No drivers available
        </div>
      )}
    </MapContainer>
      </div>
  );
};

export default MyMap;
