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
    List,
    ListItem,
    ListItemIcon,
    ListItemText,
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import StorageIcon from '@mui/icons-material/Storage';
import SchoolIcon from '@mui/icons-material/School';
import SearchIcon from '@mui/icons-material/Search';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import DescriptionIcon from '@mui/icons-material/Description';
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
                                
                                {/* Active Features */}
                                <Box sx={{ mb: 3 }}>
                                    <Typography variant="h6" gutterBottom>
                                        Active Features
                                    </Typography>
                                    <List dense>
                                        <ListItem>
                                            <ListItemIcon>
                                                <AutoAwesomeIcon color="primary" />
                                            </ListItemIcon>
                                            <ListItemText 
                                                primary="Multi-Engine Search"
                                                secondary="Aggregates results from Vector DB and Semantic Search"
                                            />
                                        </ListItem>
                                        <ListItem>
                                            <ListItemIcon>
                                                <DescriptionIcon color="primary" />
                                            </ListItemIcon>
                                            <ListItemText 
                                                primary="LangChain Document Chunking"
                                                secondary="500-char chunks with 50-char overlap for better vectorization"
                                            />
                                        </ListItem>
                                        <ListItem>
                                            <ListItemIcon>
                                                <SearchIcon color="primary" />
                                            </ListItemIcon>
                                            <ListItemText 
                                                primary="Message-Only Classification"
                                                secondary="No service or category input required"
                                            />
                                        </ListItem>
                                    </List>
                                </Box>

                                <Divider sx={{ my: 2 }} />
                                
                                <Grid container spacing={3}>
                                    <Grid item xs={12} md={6}>
                                        <Box sx={{ mb: 2 }}>
                                            <Typography variant="body2" color="text.secondary" gutterBottom>
                                                Classification Methods
                                            </Typography>
                                            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                                                <Chip label="Vector Database" color="primary" size="small" />
                                                <Chip label="Semantic Search" color="primary" size="small" />
                                            </Box>
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
                                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                            ChromaDB with dual collections for training data and user feedback
                                        </Typography>
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
                                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                            System learns from user corrections via feedback collection
                                        </Typography>
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
