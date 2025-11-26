import React from 'react';
import {
    Card,
    CardContent,
    Typography,
    Divider,
    Alert,
    Box,
    Button,
    Grid,
    Chip,
    ButtonGroup,
} from '@mui/material';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import ThumbUpIcon from '@mui/icons-material/ThumbUp';
import ThumbDownIcon from '@mui/icons-material/ThumbDown';
import SpeedIcon from '@mui/icons-material/Speed';

function ClassificationResult({
    result,
    feedbackGiven,
    onPositiveFeedback,
    onNegativeFeedback,
    onCopyPath,
    getConfidenceColor,
    responseTime,
}) {
    if (!result) {
        return null;
    }

    return (
        <Card elevation={3}>
            <CardContent>
                <Typography variant="h6" gutterBottom>
                    Classification Result
                    {result.multi_search && (
                        <Chip label="Multi-Engine" color="success" size="small" sx={{ ml: 2 }} />
                    )}
                    {responseTime && (
                        <Chip 
                            icon={<SpeedIcon />}
                            label={`${responseTime.toFixed(0)}ms`} 
                            color={responseTime < 10 ? 'success' : responseTime < 50 ? 'primary' : 'default'}
                            size="small" 
                            sx={{ ml: 1 }} 
                        />
                    )}
                </Typography>
                <Divider sx={{ mb: 2 }} />

                {result.warning && (
                    <Alert severity="warning" sx={{ mb: 2 }}>
                        {result.warning}
                    </Alert>
                )}

                {result.multi_search && result.consensus_count && (
                    <Alert severity="info" sx={{ mb: 2 }}>
                        <Typography variant="body2">
                            <strong>Consensus:</strong> {result.consensus_count} out of{' '}
                            {result.total_methods} methods agree
                            {result.consensus_methods && ` (${result.consensus_methods.join(', ')})`}
                        </Typography>
                    </Alert>
                )}

                <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                        Documentation Path
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography
                            variant="body1"
                            sx={{
                                fontFamily: 'monospace',
                                bgcolor: 'grey.100',
                                p: 1,
                                borderRadius: 1,
                                flexGrow: 1,
                            }}
                        >
                            {result.doc_path}
                        </Typography>
                        <Button size="small" startIcon={<ContentCopyIcon />} onClick={onCopyPath}>
                            Copy
                        </Button>
                    </Box>
                </Box>

                <Grid container spacing={2}>
                    <Grid item xs={12} sm={4}>
                        <Typography variant="body2" color="text.secondary">
                            Confidence
                        </Typography>
                        <Chip
                            label={`${result.confidence.toFixed(2)}%`}
                            color={getConfidenceColor(result.confidence)}
                            sx={{ mt: 0.5 }}
                        />
                    </Grid>

                    <Grid item xs={12} sm={4}>
                        <Typography variant="body2" color="text.secondary">
                            Source
                        </Typography>
                        <Chip label={result.source} color="primary" sx={{ mt: 0.5 }} />
                    </Grid>

                    <Grid item xs={12} sm={4}>
                        <Typography variant="body2" color="text.secondary">
                            Method
                        </Typography>
                        <Chip label="HYBRID_CUSTOM" color="secondary" sx={{ mt: 0.5 }} />
                    </Grid>
                </Grid>

                {result.root_cause && (
                    <Box sx={{ mt: 2 }}>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                            Root Cause
                        </Typography>
                        <Typography variant="body1">{result.root_cause}</Typography>
                    </Box>
                )}

                <Divider sx={{ my: 3 }} />

                <Box>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                        Was this result helpful?
                    </Typography>
                    <ButtonGroup variant="outlined" sx={{ mt: 1 }}>
                        <Button
                            startIcon={<ThumbUpIcon />}
                            onClick={onPositiveFeedback}
                            disabled={feedbackGiven !== null}
                            color={feedbackGiven === 'positive' ? 'success' : 'inherit'}
                        >
                            Yes, Correct
                        </Button>
                        <Button
                            startIcon={<ThumbDownIcon />}
                            onClick={onNegativeFeedback}
                            disabled={feedbackGiven !== null}
                            color={feedbackGiven === 'negative' ? 'error' : 'inherit'}
                        >
                            No, Incorrect
                        </Button>
                    </ButtonGroup>
                </Box>
            </CardContent>
        </Card>
    );
}

export default ClassificationResult;
