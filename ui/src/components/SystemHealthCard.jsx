import React from 'react';
import {
    Card,
    CardContent,
    Box,
    Typography,
    List,
    ListItem,
    ListItemIcon,
    ListItemText,
    Divider,
    Grid,
    Chip,
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import StorageIcon from '@mui/icons-material/Storage';
import SchoolIcon from '@mui/icons-material/School';

function SystemHealthCard({ status }) {
    return (
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
    );
}

export default SystemHealthCard;
