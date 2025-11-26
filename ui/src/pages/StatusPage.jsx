import React from 'react';
import { Container, Typography, Box, Grid, Alert, LinearProgress } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { getStatus } from '../services/api';
import SystemHealthCard from '../components/SystemHealthCard';
import { MongoDBCard, LearnedKnowledgeCard, MLFeaturesCard } from '../components/StatusCards';

function StatusPage() {
    const { data: status, isLoading, error } = useQuery({
        queryKey: ['status'],
        queryFn: getStatus,
        refetchInterval: 5000,
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
                        <SystemHealthCard status={status} />

                        <Grid container spacing={3}>
                            <Grid item xs={12} md={4}>
                                <MongoDBCard />
                            </Grid>

                            <Grid item xs={12} md={4}>
                                <LearnedKnowledgeCard status={status} />
                            </Grid>

                            <Grid item xs={12} md={4}>
                                <MLFeaturesCard />
                            </Grid>
                        </Grid>
                    </>
                )}
            </Box>
        </Container>
    );
}

export default StatusPage;
