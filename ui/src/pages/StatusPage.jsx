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
                                                primary="Hybrid Custom Search Engine"
                                                secondary="TF-IDF + BM25 probabilistic ranking with adaptive feedback loop"
                                            />
                                        </ListItem>
                                        <ListItem>
                                            <ListItemIcon>
                                                <StorageIcon color="primary" />
                                            </ListItemIcon>
                                            <ListItemText 
                                                primary="MongoDB Vector Store"
                                                secondary="Persistent vector storage with automatic reindexing on document changes"
                                            />
                                        </ListItem>
                                        <ListItem>
                                            <ListItemIcon>
                                                <SchoolIcon color="primary" />
                                            </ListItemIcon>
                                            <ListItemText 
                                                primary="Reinforcement Learning"
                                                secondary="Learns from user feedback to improve confidence over time"
                                            />
                                        </ListItem>
                                        <ListItem>
                                            <ListItemIcon>
                                                <SearchIcon color="primary" />
                                            </ListItemIcon>
                                            <ListItemText 
                                                primary="100% Custom ML Implementation"
                                                secondary="No blackbox libraries - complete algorithmic transparency"
                                            />
                                        </ListItem>
                                    </List>
                                </Box>

                                <Divider sx={{ my: 2 }} />
                                
                                <Grid container spacing={3}>
                                    <Grid item xs={12} md={6}>
                                        <Box sx={{ mb: 2 }}>
                                            <Typography variant="body2" color="text.secondary" gutterBottom>
                                                Search Engine
                                            </Typography>
                                            <Chip label={status.model_status || 'Not Available'} color="primary" size="small" />
                                        </Box>
                                    </Grid>
                                    <Grid item xs={12} md={6}>
                                        <Box sx={{ mb: 2 }}>
                                            <Typography variant="body2" color="text.secondary" gutterBottom>
                                                System Status
                                            </Typography>
                                            <Chip
                                                label={status.healthy ? 'Operational' : 'Degraded'}
                                                color={status.healthy ? 'success' : 'error'}
                                            />
                                        </Box>
                                    </Grid>
                                </Grid>
                            </CardContent>
                        </Card>

                        <Grid container spacing={3}>
                            <Grid item xs={12} md={4}>
                                <Card>
                                    <CardContent>
                                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                                            <StorageIcon color="primary" sx={{ mr: 1 }} />
                                            <Typography variant="h6">MongoDB</Typography>
                                        </Box>
                                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                            Persistent vector storage and feedback database
                                        </Typography>
                                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                            <Typography variant="body2" color="text.secondary">
                                                Collections
                                            </Typography>
                                            <Chip label="10" color="primary" size="small" />
                                        </Box>
                                        <Typography variant="caption" color="text.secondary" display="block">
                                            4 vector + 6 feedback collections
                                        </Typography>
                                    </CardContent>
                                </Card>
                            </Grid>

                            <Grid item xs={12} md={4}>
                                <Card>
                                    <CardContent>
                                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                                            <SchoolIcon color="secondary" sx={{ mr: 1 }} />
                                            <Typography variant="h6">Learned Knowledge</Typography>
                                        </Box>
                                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                            System learns from user corrections via adaptive feedback
                                        </Typography>
                                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                            <Typography variant="body2" color="text.secondary">
                                                Total Corrections
                                            </Typography>
                                            <Chip label={status.learned_corrections || 0} color="secondary" size="small" />
                                        </Box>
                                        {status.feedback_loop && (
                                            <Typography variant="caption" color="text.secondary" display="block">
                                                {status.feedback_loop.total_predictions || 0} predictions tracked
                                            </Typography>
                                        )}
                                    </CardContent>
                                </Card>
                            </Grid>

                            <Grid item xs={12} md={4}>
                                <Card>
                                    <CardContent>
                                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                                            <AutoAwesomeIcon color="success" sx={{ mr: 1 }} />
                                            <Typography variant="h6">ML Features</Typography>
                                        </Box>
                                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                            Custom implementations with full transparency
                                        </Typography>
                                        <List dense sx={{ p: 0 }}>
                                            <ListItem sx={{ px: 0, py: 0.5 }}>
                                                <Typography variant="caption">• TF-IDF Vectorization</Typography>
                                            </ListItem>
                                            <ListItem sx={{ px: 0, py: 0.5 }}>
                                                <Typography variant="caption">• BM25 Ranking</Typography>
                                            </ListItem>
                                            <ListItem sx={{ px: 0, py: 0.5 }}>
                                                <Typography variant="caption">• Cosine Similarity</Typography>
                                            </ListItem>
                                            <ListItem sx={{ px: 0, py: 0.5 }}>
                                                <Typography variant="caption">• Query Pattern Learning</Typography>
                                            </ListItem>
                                        </List>
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
