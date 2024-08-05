import React, { useEffect, useState } from 'react';

function Map() {
    const [mapData, setMapData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let isMounted = true;  // Track if the component is mounted

        const fetchMapData = async () => {
            try {
                const response = await fetch('http://127.0.0.1:5000/map');
                const data = await response.text();
                if (isMounted) {
                    setMapData(data);
                    setLoading(false);
                }
            } catch (error) {
                console.error('Error fetching map data:', error);
                if (isMounted) {
                    setLoading(false);
                }
            }
        };

        fetchMapData();

        return () => {
            isMounted = false;  // Cleanup function to prevent state update if unmounted
        };
    }, []);

    if (loading) {
        return <p>Loading map...</p>;
    }

    return (
        <div className="App">
            <h1>Map Viewer</h1>
            {mapData && <div dangerouslySetInnerHTML={{ __html: mapData }} />}
        </div>
    );
}

export default Map;
