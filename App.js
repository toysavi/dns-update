import React, { useState, useEffect } from "react";
import CSVReader from "react-csv-reader";
import axios from "axios";
import { Table, Button, ProgressBar, Form, Container, Row, Col } from "react-bootstrap";
import "bootstrap/dist/css/bootstrap.min.css";

const App = () => {
    const [csvData, setCsvData] = useState([]);
    const [filteredData, setFilteredData] = useState([]);
    const [selectedRecordType, setSelectedRecordType] = useState("Both");
    const [progress, setProgress] = useState(0);
    const [statusMessage, setStatusMessage] = useState("");
    const [showUpdated, setShowUpdated] = useState(false);

    useEffect(() => {
        setFilteredData(csvData);
    }, [csvData]);

    // Handle CSV Upload
    const handleFileUpload = (data) => {
        setCsvData(data);
        setFilteredData(data);
    };

    // Handle Record Type Selection
    const handleCheckboxChange = (event) => {
        setSelectedRecordType(event.target.value);
    };

    // Handle Search/Filter
    const handleSearch = (event) => {
        const query = event.target.value.toLowerCase();
        const filtered = csvData.filter(
            (row) => row[0].toLowerCase().includes(query) || row[1].includes(query) || row[2].toLowerCase().includes(query)
        );
        setFilteredData(filtered);
    };

    // Apply DNS Update
    const applyUpdate = async () => {
        setProgress(10);
        setStatusMessage("Updating DNS records...");

        try {
            const response = await axios.post("http://localhost:5000/update-dns", {
                records: csvData,
                recordType: selectedRecordType,
            });

            setProgress(100);
            setStatusMessage(response.data.message);
            setShowUpdated(true);
        } catch (error) {
            setStatusMessage("Update failed: " + error.message);
        }
    };

    // Clear Data
    const clearData = () => {
        setCsvData([]);
        setFilteredData([]);
        setProgress(0);
        setStatusMessage("");
        setShowUpdated(false);
    };

    return (
        <Container>
            <Row className="mt-3">
                <Col>
                    <h4>DNS Update Tool</h4>
                </Col>
            </Row>

            {/* CSV Upload */}
            <Row>
                <Col>
                    <CSVReader onFileLoaded={handleFileUpload} />
                </Col>
            </Row>

            {/* Checkboxes */}
            <Row>
                <Col>
                    <Form.Check type="radio" label="A Record" value="A" checked={selectedRecordType === "A"} onChange={handleCheckboxChange} />
                    <Form.Check type="radio" label="CNAME" value="CNAME" checked={selectedRecordType === "CNAME"} onChange={handleCheckboxChange} />
                    <Form.Check type="radio" label="Both" value="Both" checked={selectedRecordType === "Both"} onChange={handleCheckboxChange} />
                </Col>
            </Row>

            {/* Search Bar */}
            <Row>
                <Col>
                    <Form.Control type="text" placeholder="Search by Name, IP, Record Type" onChange={handleSearch} />
                </Col>
            </Row>

            {/* Apply & Clear Buttons */}
            <Row className="mt-2">
                <Col>
                    <Button variant="primary" onClick={applyUpdate}>Apply Update</Button>
                    <Button variant="danger" onClick={clearData} className="ms-2">Clear</Button>
                </Col>
            </Row>

            {/* Progress Bar */}
            {progress > 0 && (
                <Row className="mt-2">
                    <Col>
                        <ProgressBar now={progress} label={`${progress}%`} />
                        <p>{statusMessage}</p>
                    </Col>
                </Row>
            )}

            {/* Table Display */}
            <Row className="mt-2">
                <Col>
                    <Table striped bordered hover>
                        <thead>
                            <tr>
                                <th>Record Type</th>
                                <th>Src. Alias</th>
                                <th>Src. Point to</th>
                                <th>Des. Alias</th>
                                <th>Des. Point to</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredData.map((row, index) => (
                                <tr key={index}>
                                    <td>{row[0]}</td>
                                    <td>{row[1]}</td>
                                    <td>{row[2]}</td>
                                    <td>{row[3]}</td>
                                    <td>{row[4]}</td>
                                    <td>{showUpdated ? "Updated" : "Pending"}</td>
                                </tr>
                            ))}
                        </tbody>
                    </Table>
                </Col>
            </Row>
        </Container>
    );
};

export default App;
