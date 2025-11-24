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

function ManageDocsPage() {
    const [docs, setDocs] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);
    const [openDialog, setOpenDialog] = useState(false);
    const [editingDoc, setEditingDoc] = useState(null);
    const [formData, setFormData] = useState({
        service: '',
        category: '',
        content: '',
        path: '',
    });

    useEffect(() => {
        fetchDocs();
    }, []);

    const fetchDocs = async () => {
        setLoading(true);
        try {
            const response = await axios.get('/api/docs');
            setDocs(response.data);
            setError(null);
        } catch (err) {
            setError('Failed to fetch documentation files');
        } finally {
            setLoading(false);
        }
    };

    const handleOpenDialog = (doc = null) => {
        if (doc) {
            setEditingDoc(doc);
            setFormData({
                service: doc.service,
                category: doc.category,
                content: doc.content,
                path: doc.path,
            });
        } else {
            setEditingDoc(null);
            setFormData({
                service: '',
                category: '',
                content: '',
                path: '',
            });
        }
        setOpenDialog(true);
    };

    const handleCloseDialog = () => {
        setOpenDialog(false);
        setEditingDoc(null);
        setFormData({
            service: '',
            category: '',
            content: '',
            path: '',
        });
    };

    const handleSave = async () => {
        try {
            if (editingDoc) {
                await axios.put(`/api/docs/${editingDoc.id}`, formData);
                setSuccess('Documentation updated successfully');
            } else {
                await axios.post('/api/docs', formData);
                setSuccess('Documentation created successfully');
            }
            handleCloseDialog();
            fetchDocs();
        } catch (err) {
            setError(err.response?.data?.error || 'Failed to save documentation');
        }
    };

    const handleDelete = async (docId) => {
        if (!window.confirm('Are you sure you want to delete this document?')) {
            return;
        }

        try {
            await axios.delete(`/api/docs/${docId}`);
            setSuccess('Documentation deleted successfully');
            fetchDocs();
        } catch (err) {
            setError('Failed to delete documentation');
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
        <Container maxWidth="lg">
            <Box sx={{ my: 4 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                    <Typography variant="h4" component="h1">
                        Manage Documentation
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                        <Button
                            variant="outlined"
                            startIcon={<RefreshIcon />}
                            onClick={fetchDocs}
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
                            Add Document
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
                                <TableCell>Service</TableCell>
                                <TableCell>Category</TableCell>
                                <TableCell>Path</TableCell>
                                <TableCell>Size</TableCell>
                                <TableCell align="right">Actions</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {docs.map((doc) => (
                                <TableRow key={doc.id}>
                                    <TableCell>
                                        <Chip label={doc.service} size="small" color="primary" />
                                    </TableCell>
                                    <TableCell>{doc.category}</TableCell>
                                    <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
                                        {doc.path}
                                    </TableCell>
                                    <TableCell>{doc.size || 'N/A'}</TableCell>
                                    <TableCell align="right">
                                        <IconButton
                                            size="small"
                                            color="primary"
                                            onClick={() => handleOpenDialog(doc)}
                                        >
                                            <EditIcon />
                                        </IconButton>
                                        <IconButton
                                            size="small"
                                            color="error"
                                            onClick={() => handleDelete(doc.id)}
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
                        {editingDoc ? 'Edit Documentation' : 'Add New Documentation'}
                    </DialogTitle>
                    <DialogContent>
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
                            <TextField
                                label="Service"
                                value={formData.service}
                                onChange={(e) => setFormData({ ...formData, service: e.target.value })}
                                fullWidth
                            />
                            <TextField
                                label="Category"
                                value={formData.category}
                                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                                fullWidth
                            />
                            <TextField
                                label="File Path"
                                value={formData.path}
                                onChange={(e) => setFormData({ ...formData, path: e.target.value })}
                                fullWidth
                                helperText="Relative path to the documentation file"
                            />
                            <TextField
                                label="Content"
                                value={formData.content}
                                onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                                fullWidth
                                multiline
                                rows={10}
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

export default ManageDocsPage;
