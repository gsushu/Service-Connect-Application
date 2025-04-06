import React, { useEffect, useState } from "react";
import axios from "axios";
import { useLocation, useNavigate } from "react-router-dom";
import CreateRequest from "./CreateRequest";
import "../styles/Home.css";
import Profile from "./Profile";
import AllServices from "./AllServices";

function Home() {
  const location = useLocation();
  const navigate = useNavigate();
  const { username } = location.state || {};

  useEffect(() => {
    if (!username) {
      navigate("/");
    }
  }, [username, navigate]);

  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios
      .get("http://localhost:8000/allrequests", { withCredentials: true })
      .then((response) => {
        setRequests(response.data);
        setLoading(false);
      })
      .catch((error) => {
        console.error("Error fetching requests:", error);
        setLoading(false);
      });
  }, []);

  const [activeRightView, setActiveRightView] = useState("createRequest");

  const handleViewAllRequests = () => {
    setActiveRightView("createRequest");
  };

  const handleProfile = () => {
    setActiveRightView("profile");
  };

  const handleViewServices = () => {
    setActiveRightView("services");
  };

  const handleLogout = async () => {
    try {
      await axios.post(
        "http://localhost:8000/logout",
        {},
        { withCredentials: true }
      );
      navigate("/");
    } catch (error) {
      console.error("Error during logout:", error);
    }
  };

  return (
    <div className="home-container">
      <div className="left-section">
        <h2>Hi, {username}!</h2>
        <br />
        <div className="button-row">
          <button onClick={handleViewAllRequests}>Create new request</button>
          <button onClick={handleProfile}>Profile</button>
          <button onClick={handleViewServices}>View Services</button>
          <button onClick={handleLogout}>Logout</button>
        </div>

        <h3>Your Requests:</h3>
        {loading ? (
          <p>Loading requests...</p>
        ) : (
          <div className="requests-list">
            {requests.length === 0 ? (
              <p>No requests found.</p>
            ) : (
              requests.map((req) => (
                <div className="request-card" key={req.request_id}>
                  <div className="request-header">
                    <span className="request-id">
                      Request #{req.request_id}
                    </span>
                    <span className={`status ${req.status}`}>{req.status}</span>
                  </div>
                  <div className="request-body">
                    <p>
                      <strong>Service ID:</strong> {req.service_id}
                    </p>
                    <p>
                      <strong>Description:</strong> {req.description}
                    </p>
                    <p>
                      <strong>Created At:</strong>{" "}
                      {new Date(req.created_at).toLocaleString()}
                    </p>
                    {req.worker_id && (
                      <p>
                        <strong>Worker ID:</strong> {req.worker_id}
                      </p>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      <div className="right-section">
        {activeRightView === "createRequest" && <CreateRequest />}
        {activeRightView === "profile" && (
          <div className="view-container">
            <Profile />
          </div>
        )}
        {activeRightView === "services" && (
          <div className="view-container">
            <AllServices />
          </div>
        )}
      </div>
    </div>
  );
}

export default Home;
