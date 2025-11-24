import React, { useState, useEffect } from 'react';
import {
    Container,
    Paper,
    Typography,
    Box,
    Button,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    IconButton,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    TextField,
    Alert,
    Chip,
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import RefreshIcon from '@mui/icons-material/Refresh';
import axios from 'axios';

function ManageDatasetPage() {
    const [records, setRecords] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);
    const [openDialog, setOpenDialog] = useState(false);
    const [editingRecord, setEditingRecord] = useState(null);
    const [formData, setFormData] = useState({
        timestamp: '',
        service: '',
        error_category: '',
        raw_input_snippet: '',
        root_cause: '',
    });

    useEffect(() => {
        fetchDataset();
    }, []);

    const fetchDataset = async () => {
        setLoading(true);
        try {
            const response = await axios.get('/api/dataset');
            setRecords(response.data);
            setError(null);
        } catch (err) {
            setError('Failed to fetch dataset');
        } finally {
            setLoading(false);
        }
    };

    const handleOpenDialog = (record = null) => {
        if (record) {
            setEditingRecord(record);
            setFormData({
                timestamp: record.timestamp,
                service: record.service,
                error_category: record.error_category,
                raw_input_snippet: record.raw_input_snippet,
                root_cause: record.root_cause,
            });
        } else {
            setEditingRecord(null);
            setFormData({
                timestamp: new Date().toISOString(),
                service: '',
                error_category: '',
                raw_input_snippet: '',
                root_cause: '',
            });
        }
        setOpenDialog(true);
    };

    const handleCloseDialog = () => {
        setOpenDialog(false);
        setEditingRecord(null);
        setFormData({
            timestamp: '',
            service: '',
            error_category: '',
            raw_input_snippet: '',
            root_cause: '',
        });
    };

    const handleSave = async () => {
        try {
            if (editingRecord) {
                await axios.put(`/api/dataset/${editingRecord.id}`, formData);
                setSuccess('Record updated successfully');
            } else {
                await axios.post('/api/dataset', formData);
                setSuccess('Record added successfully');
            }
            handleCloseDialog();
            fetchDataset();
        } catch (err) {
            setError(err.response?.data?.error || 'Failed to save record');
        }
    };

    const handleDelete = async (recordId) => {
        if (!window.confirm('Are you sure you want to delete this record?')) {
            return;
        }

        try {
            await axios.delete(`/api/dataset/${recordId}`);
            setSuccess('Record deleted successfully');
            fetchDataset();
        } catch (err) {
            setError('Failed to delete record');
        }
    };

    const handleUpdateKB = async () => {
        try {
            await axios.post('/api/update-kb');
            setSuccess('Knowledge base updated successfully');
        } catch (err) {
            setError('Failed to update knowledge base');
        }
    };

    return (
        <Container maxWidth="xl">
            <Box sx={{ my: 4 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                    <Typography variant="h4" component="h1">
                        Manage Training Dataset
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                        <Button
                            variant="outlined"
                            startIcon={<RefreshIcon />}
                            onClick={fetchDataset}
                            disabled={loading}
                        >
                            Refresh
                        </Button>
                        <Button
                            variant="contained"
                            color="secondary"
                            onClick={handleUpdateKB}
                        >
                            Update Knowledge Base
                        </Button>
                        <Button
                            variant="contained"
                            startIcon={<AddIcon />}
                            onClick={() => handleOpenDialog()}
                        >
                            Add Record
                        </Button>
                    </Box>
                </Box>

                {error && (
                    <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
                        {error}
                    </Alert>
                )}

                {success && (
                    <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
                        {success}
                    </Alert>
                )}

                <TableContainer component={Paper}>
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableCell>Timestamp</TableCell>
                                <TableCell>Service</TableCell>
                                <TableCell>Category</TableCell>
                                <TableCell>Error Snippet</TableCell>
                                <TableCell>Root Cause</TableCell>
                                <TableCell align="right">Actions</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {records.map((record) => (
                                <TableRow key={record.id}>
                                    <TableCell sx={{ fontSize: '0.75rem' }}>
                                        {new Date(record.timestamp).toLocaleString()}
                                    </TableCell>
                                    <TableCell>
                                        <Chip label={record.service} size="small" color="primary" />
                                    </TableCell>
                                    <TableCell>
                                        <Chip label={record.error_category} size="small" />
                                    </TableCell>
                                    <TableCell sx={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                        {record.raw_input_snippet}
                                    </TableCell>
                                    <TableCell sx={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                        {record.root_cause}
                                    </TableCell>
                                    <TableCell align="right">
                                        <IconButton
                                            size="small"
                                            color="primary"
                                            onClick={() => handleOpenDialog(record)}
                                        >
                                            <EditIcon />
                                        </IconButton>
                                        <IconButton
                                            size="small"
                                            color="error"
                                            onClick={() => handleDelete(record.id)}
                                        >
                                            <DeleteIcon />
                                        </IconButton>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </TableContainer>

                <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
                    <DialogTitle>
                        {editingRecord ? 'Edit Record' : 'Add New Record'}
                    </DialogTitle>
                    <DialogContent>
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
                            <TextField
                                label="Service"
                                value={formData.service}
                                onChange={(e) => setFormData({ ...formData, service: e.target.value })}
                                fullWidth
                                required
                            />
                            <TextField
                                label="Error Category"
                                value={formData.error_category}
                                onChange={(e) => setFormData({ ...formData, error_category: e.target.value })}
                                fullWidth
                                required
                            />
                            <TextField
                                label="Raw Input Snippet"
                                value={formData.raw_input_snippet}
                                onChange={(e) => setFormData({ ...formData, raw_input_snippet: e.target.value })}
                                fullWidth
                                multiline
                                rows={3}
                                required
                            />
                            <TextField
                                label="Root Cause"
                                value={formData.root_cause}
                                onChange={(e) => setFormData({ ...formData, root_cause: e.target.value })}
                                fullWidth
                                multiline
                                rows={2}
                                required
                            />
                        </Box>
                    </DialogContent>
                    <DialogActions>
                        <Button onClick={handleCloseDialog}>Cancel</Button>
                        <Button onClick={handleSave} variant="contained">
                            Save
                        </Button>
                    </DialogActions>
                </Dialog>
            </Box>
        </Container>
    );
}

export default ManageDatasetPage;
