import React, { useEffect, useState } from 'react';
import {
    Card,
    CardContent,
    Box,
    Typography,
    Chip,
    List,
    ListItem,
} from '@mui/material';
import StorageIcon from '@mui/icons-material/Storage';
import SchoolIcon from '@mui/icons-material/School';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';

export function MongoDBCard() {
    const [mongoInfo, setMongoInfo] = useState({
        collections: 10,
        vector_collections: 4,
        feedback_collections: 6,
        description: 'Persistent vector storage and feedback database'
    });

    useEffect(() => {
        fetch('/api/config')
            .then(res => res.json())
            .then(data => {
                if (data.mongodb) {
                    setMongoInfo(data.mongodb);
                }
            })
            .catch(err => console.error('Failed to fetch MongoDB config:', err));
    }, []);

    return (
        <Card>
            <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <StorageIcon color="primary" sx={{ mr: 1 }} />
                    <Typography variant="h6">MongoDB</Typography>
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {mongoInfo.description}
                </Typography>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                        Collections
                    </Typography>
                    <Chip label={mongoInfo.collections} color="primary" size="small" />
                </Box>
                <Typography variant="caption" color="text.secondary" display="block">
                    {mongoInfo.vector_collections} vector + {mongoInfo.feedback_collections} feedback collections
                </Typography>
            </CardContent>
        </Card>
    );
}

export function LearnedKnowledgeCard({ status }) {
    return (
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
    );
}

export function MLFeaturesCard() {
    const [features, setFeatures] = useState([
        'TF-IDF Vectorization',
        'BM25 Ranking',
        'Cosine Similarity',
        'Query Pattern Learning',
    ]);

    useEffect(() => {
        fetch('/api/config')
            .then(res => res.json())
            .then(data => {
                if (data.ml_features && data.ml_features.length > 0) {
                    setFeatures(data.ml_features);
                }
            })
            .catch(err => console.error('Failed to fetch ML features:', err));
    }, []);

    return (
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
                    {features.map((feature, idx) => (
                        <ListItem key={idx} sx={{ px: 0, py: 0.5 }}>
                            <Typography variant="caption">• {feature}</Typography>
                        </ListItem>
                    ))}
                </List>
            </CardContent>
        </Card>
    );
}
