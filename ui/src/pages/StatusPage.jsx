import React from 'react';
import {
    Container,
    Paper,
    Typography,
    Box,
    Grid,
    Card,
    CardContent,
    Chip,
    Alert,
    LinearProgress,
    Divider,
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import StorageIcon from '@mui/icons-material/Storage';
import SchoolIcon from '@mui/icons-material/School';
import { useQuery } from '@tanstack/react-query';
import { getStatus } from '../services/api';

function StatusPage() {
    const { data: status, isLoading, error } = useQuery({
        queryKey: ['status'],
        queryFn: getStatus,
        refetchInterval: 5000, // Refresh every 5 seconds
    });

    if (isLoading && !status) {
        return (
            <Container maxWidth="lg">
                <Box sx={{ my: 4 }}>
                    <LinearProgress />
                </Box>
            </Container>
        );
    }

    return (
        <Container maxWidth="lg">
            <Box sx={{ my: 4 }}>
                <Typography variant="h4" component="h1" gutterBottom>
                    System Status
                </Typography>

                {error && (
                    <Alert severity="error" sx={{ mb: 2 }}>
                        {error.message || 'Failed to fetch system status'}
                    </Alert>
                )}

                {status && (
                    <>
                        <Card sx={{ mb: 3 }}>
                            <CardContent>
                                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                                    {status.healthy ? (
                                        <CheckCircleIcon color="success" sx={{ mr: 1, fontSize: 40 }} />
                                    ) : (
                                        <ErrorIcon color="error" sx={{ mr: 1, fontSize: 40 }} />
                                    )}
                                    <Box>
                                        <Typography variant="h5">
                                            System {status.healthy ? 'Healthy' : 'Unhealthy'}
                                        </Typography>
                                        <Typography variant="body2" color="text.secondary">
                                            Last updated: {new Date().toLocaleString()}
                                        </Typography>
                                    </Box>
                                </Box>
                                <Divider sx={{ my: 2 }} />
                                <Grid container spacing={3}>
                                    <Grid item xs={12} md={6}>
                                        <Box sx={{ mb: 2 }}>
                                            <Typography variant="body2" color="text.secondary" gutterBottom>
                                                Model Status
                                            </Typography>
                                            <Typography variant="body1">{status.model_status}</Typography>
                                        </Box>
                                    </Grid>
                                    <Grid item xs={12} md={6}>
                                        <Box sx={{ mb: 2 }}>
                                            <Typography variant="body2" color="text.secondary" gutterBottom>
                                                Vector DB Status
                                            </Typography>
                                            <Chip
                                                label={status.vector_db_status}
                                                color={status.vector_db_status === 'Ready' ? 'success' : 'error'}
                                            />
                                        </Box>
                                    </Grid>
                                </Grid>
                            </CardContent>
                        </Card>

                        <Grid container spacing={3}>
                            <Grid item xs={12} md={6}>
                                <Card>
                                    <CardContent>
                                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                                            <StorageIcon color="primary" sx={{ mr: 1 }} />
                                            <Typography variant="h6">Vector Database</Typography>
                                        </Box>
                                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                            <Typography variant="body2" color="text.secondary">
                                                Total Records
                                            </Typography>
                                            <Chip label={status.vector_db_records} color="primary" size="small" />
                                        </Box>
                                    </CardContent>
                                </Card>
                            </Grid>

                            <Grid item xs={12} md={6}>
                                <Card>
                                    <CardContent>
                                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                                            <SchoolIcon color="secondary" sx={{ mr: 1 }} />
                                            <Typography variant="h6">Learned Knowledge</Typography>
                                        </Box>
                                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                            <Typography variant="body2" color="text.secondary">
                                                User Corrections
                                            </Typography>
                                            <Chip label={status.learned_corrections} color="secondary" size="small" />
                                        </Box>
                                    </CardContent>
                                </Card>
                            </Grid>
                        </Grid>
                    </>
                )}
            </Box>
        </Container>
    );
}

export default StatusPage;
