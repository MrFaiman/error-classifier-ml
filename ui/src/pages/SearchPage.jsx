import React, { useState } from 'react';
import {
    Container,
    Paper,
    TextField,
    Button,
    Box,
    Typography,
    Card,
    CardContent,
    Chip,
    Alert,
    CircularProgress,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Grid,
    Divider,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    ButtonGroup,
    Accordion,
    AccordionSummary,
    AccordionDetails,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import ThumbUpIcon from '@mui/icons-material/ThumbUp';
import ThumbDownIcon from '@mui/icons-material/ThumbDown';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import DescriptionIcon from '@mui/icons-material/Description';
import { useMutation, useQuery } from '@tanstack/react-query';
import { classifyError, teachCorrection, getDocContent } from '../services/api';

function SearchPage() {
    const [errorInput, setErrorInput] = useState('');
    const [method, setMethod] = useState('VECTOR_DB');
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);
    const [feedbackGiven, setFeedbackGiven] = useState(null);
    const [openCorrectionDialog, setOpenCorrectionDialog] = useState(false);
    const [correctPath, setCorrectPath] = useState('');
    const [feedbackSuccess, setFeedbackSuccess] = useState(null);

    // Mutation for classification
    const classifyMutation = useMutation({
        mutationFn: classifyError,
        onSuccess: (data) => {
            setResult(data);
            setError(null);
            setFeedbackGiven(null);
            setFeedbackSuccess(null);
        },
        onError: (err) => {
            setError(err.response?.data?.error || 'Failed to classify error');
            setResult(null);
        },
    });

    // Mutation for teaching correction
    const teachMutation = useMutation({
        mutationFn: teachCorrection,
        onSuccess: () => {
            setFeedbackSuccess('Correction saved! The system will learn from this.');
            setOpenCorrectionDialog(false);
            setCorrectPath('');
        },
        onError: (err) => {
            setError(err.response?.data?.error || 'Failed to save correction');
        },
    });

    // Query for fetching documentation content
    const { data: docContent, isLoading: isLoadingDoc } = useQuery({
        queryKey: ['docContent', result?.doc_path],
        queryFn: () => getDocContent(result.doc_path),
        enabled: !!result?.doc_path,
        retry: 1,
    });

    const handleSearch = () => {
        if (!errorInput.trim()) {
            setError('Please enter an error log');
            return;
        }

        classifyMutation.mutate({
            error_log: errorInput,
            method: method,
        });
    };

    const handlePositiveFeedback = () => {
        setFeedbackGiven('positive');
        setFeedbackSuccess('Thank you for your feedback!');
    };

    const handleNegativeFeedback = () => {
        setFeedbackGiven('negative');
        setOpenCorrectionDialog(true);
    };

    const handleSubmitCorrection = () => {
        if (!correctPath.trim()) {
            setError('Please enter the correct documentation path');
            return;
        }

        teachMutation.mutate({
            error_text: errorInput,
            correct_doc_path: correctPath,
        });
    };

    const handleCloseCorrectionDialog = () => {
        setOpenCorrectionDialog(false);
        setCorrectPath('');
        setFeedbackGiven(null);
    };

    const handleCopyPath = () => {
        if (result?.doc_path) {
            navigator.clipboard.writeText(result.doc_path);
        }
    };

    const getConfidenceColor = (confidence) => {
        if (confidence >= 80) return 'success';
        if (confidence >= 60) return 'warning';
        return 'error';
    };

    return (
        <Container maxWidth="lg">
            <Box sx={{ my: 4 }}>
                <Typography variant="h4" component="h1" gutterBottom align="center">
                    Error Classification Search
                </Typography>
                <Typography variant="body1" color="text.secondary" align="center" sx={{ mb: 4 }}>
                    Enter any error log (full or partial) to find the relevant documentation
                </Typography>

                <Paper elevation={3} sx={{ p: 4, mb: 4 }}>
                    <Grid container spacing={3}>
                        <Grid item xs={12}>
                            <FormControl fullWidth>
                                <InputLabel>Classification Method</InputLabel>
                                <Select
                                    value={method}
                                    label="Classification Method"
                                    onChange={(e) => setMethod(e.target.value)}
                                >
                                    <MenuItem value="VECTOR_DB">Vector Database (with Learning)</MenuItem>
                                    <MenuItem value="SEMANTIC_SEARCH">Semantic Search</MenuItem>
                                    <MenuItem value="RANDOM_FOREST">Random Forest ML</MenuItem>
                                </Select>
                            </FormControl>
                        </Grid>

                        <Grid item xs={12}>
                            <TextField
                                fullWidth
                                multiline
                                rows={6}
                                label="Error Log"
                                placeholder="Paste full or partial error log, e.g.:\n2025-11-24T08:00:01Z,SkyGuard,SCHEMA_VALIDATION,signal_strength: 999,Sensor Glitch - Value out of range (0-100)\n\nOr just partial:\nsignal_strength: 999\nSensor Glitch"
                                value={errorInput}
                                onChange={(e) => setErrorInput(e.target.value)}
                                variant="outlined"
                            />
                        </Grid>

                        <Grid item xs={12}>
                            <Button
                                fullWidth
                                variant="contained"
                                size="large"
                                startIcon={classifyMutation.isPending ? <CircularProgress size={20} color="inherit" /> : <SearchIcon />}
                                onClick={handleSearch}
                                disabled={classifyMutation.isPending}
                            >
                                {classifyMutation.isPending ? 'Classifying...' : 'Classify Error'}
                            </Button>
                        </Grid>
                    </Grid>
                </Paper>

                {error && (
                    <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
                        {error}
                    </Alert>
                )}

                {feedbackSuccess && (
                    <Alert severity="success" sx={{ mb: 2 }} onClose={() => setFeedbackSuccess(null)}>
                        {feedbackSuccess}
                    </Alert>
                )}

                {result && (
                    <Card elevation={3}>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Classification Result
                            </Typography>
                            <Divider sx={{ mb: 2 }} />

                            {result.warning && (
                                <Alert severity="warning" sx={{ mb: 2 }}>
                                    {result.warning}
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
                                    <Button
                                        size="small"
                                        startIcon={<ContentCopyIcon />}
                                        onClick={handleCopyPath}
                                    >
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
                                    <Chip label={method} color="secondary" sx={{ mt: 0.5 }} />
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

                            {/* Documentation Preview */}
                            <Box sx={{ mt: 3 }}>
                                <Accordion>
                                    <AccordionSummary
                                        expandIcon={<ExpandMoreIcon />}
                                        aria-controls="doc-preview-content"
                                        id="doc-preview-header"
                                    >
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                            <DescriptionIcon color="primary" />
                                            <Typography variant="body1" fontWeight="medium">
                                                Documentation Preview
                                            </Typography>
                                        </Box>
                                    </AccordionSummary>
                                    <AccordionDetails>
                                        {isLoadingDoc ? (
                                            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                                                <CircularProgress size={30} />
                                            </Box>
                                        ) : docContent?.content ? (
                                            <Paper
                                                variant="outlined"
                                                sx={{
                                                    p: 2,
                                                    bgcolor: 'grey.50',
                                                    maxHeight: 400,
                                                    overflow: 'auto',
                                                }}
                                            >
                                                <Typography
                                                    component="pre"
                                                    sx={{
                                                        fontFamily: 'monospace',
                                                        fontSize: '0.875rem',
                                                        whiteSpace: 'pre-wrap',
                                                        wordBreak: 'break-word',
                                                        m: 0,
                                                    }}
                                                >
                                                    {docContent.content}
                                                </Typography>
                                            </Paper>
                                        ) : (
                                            <Alert severity="warning">
                                                Unable to load documentation content
                                            </Alert>
                                        )}
                                    </AccordionDetails>
                                </Accordion>
                            </Box>

                            <Divider sx={{ my: 3 }} />

                            <Box>
                                <Typography variant="body2" color="text.secondary" gutterBottom>
                                    Was this result helpful?
                                </Typography>
                                <ButtonGroup variant="outlined" sx={{ mt: 1 }}>
                                    <Button
                                        startIcon={<ThumbUpIcon />}
                                        onClick={handlePositiveFeedback}
                                        disabled={feedbackGiven !== null}
                                        color={feedbackGiven === 'positive' ? 'success' : 'inherit'}
                                    >
                                        Yes, Correct
                                    </Button>
                                    <Button
                                        startIcon={<ThumbDownIcon />}
                                        onClick={handleNegativeFeedback}
                                        disabled={feedbackGiven !== null}
                                        color={feedbackGiven === 'negative' ? 'error' : 'inherit'}
                                    >
                                        No, Incorrect
                                    </Button>
                                </ButtonGroup>
                            </Box>
                        </CardContent>
                    </Card>
                )}

                <Dialog open={openCorrectionDialog} onClose={handleCloseCorrectionDialog} maxWidth="sm" fullWidth>
                    <DialogTitle>Provide Correct Documentation Path</DialogTitle>
                    <DialogContent>
                        <Box sx={{ mt: 2 }}>
                            <Typography variant="body2" color="text.secondary" gutterBottom>
                                Help us improve! Please enter the correct documentation path for this error.
                            </Typography>
                            <TextField
                                fullWidth
                                label="Correct Documentation Path"
                                placeholder="e.g., dataset/docs/services/logitrack/SECURITY_ALERT.md"
                                value={correctPath}
                                onChange={(e) => setCorrectPath(e.target.value)}
                                sx={{ mt: 2 }}
                                helperText="The system will learn from your correction"
                            />
                        </Box>
                    </DialogContent>
                    <DialogActions>
                        <Button onClick={handleCloseCorrectionDialog}>Cancel</Button>
                        <Button onClick={handleSubmitCorrection} variant="contained" color="primary">
                            Submit Correction
                        </Button>
                    </DialogActions>
                </Dialog>
            </Box>
        </Container>
    );
}

export default SearchPage;
