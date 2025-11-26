import React from 'react';
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
    return (
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
    const features = [
        'TF-IDF Vectorization',
        'BM25 Ranking',
        'Cosine Similarity',
        'Query Pattern Learning',
    ];

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
