import React, { useEffect, useState } from "react";
import "../styles/AllServices.css";
import axios from "axios";

const AllServices = () => {
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios
      .get("http://localhost:8000/allservices", { withCredentials: true })
      .then((response) => {
        setServices(response.data);
        setLoading(false);
      })
      .catch((error) => {
        console.error("Error fetching all services:", error);
        setLoading(false);
      });
  }, []);

  return (
    <div className="all-services-container">
      <h2>All Services</h2>
      {loading ? (
        <p>Loading services...</p>
      ) : services.length === 0 ? (
        <p>No services found.</p>
      ) : (
        <div className="services-list">
          {services.map((service) => (
            <div className="service-card" key={service.service_id}>
              <h3>{service.name}</h3>
              <p>{service.description}</p>
              <p>
                {" "}
                <strong> Service id: </strong>
                {service.service_id}{" "}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AllServices;
