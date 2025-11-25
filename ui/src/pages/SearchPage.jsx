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
    Switch,
    FormControlLabel,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import ThumbUpIcon from '@mui/icons-material/ThumbUp';
import ThumbDownIcon from '@mui/icons-material/ThumbDown';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import DescriptionIcon from '@mui/icons-material/Description';
import { useMutation, useQuery } from '@tanstack/react-query';
import { classifyError, teachCorrection, getDocContent, getSearchEnginesComparison } from '../services/api';
import SearchInput from '../components/SearchInput';

function SearchPage() {
    const [errorInput, setErrorInput] = useState('');
    const [method, setMethod] = useState('VECTOR_DB');
    const [multiSearch, setMultiSearch] = useState(true); // Auto-enabled by default
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);
    const [feedbackGiven, setFeedbackGiven] = useState(null);
    const [openCorrectionDialog, setOpenCorrectionDialog] = useState(false);
    const [correctPath, setCorrectPath] = useState('');
    const [feedbackSuccess, setFeedbackSuccess] = useState(null);
    const [showComparison, setShowComparison] = useState(false);

    // Query for search engines comparison
    const { data: comparisonData } = useQuery({
        queryKey: ['searchEnginesComparison'],
        queryFn: getSearchEnginesComparison,
        staleTime: Infinity, // This data doesn't change often
    });

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
            setError('Please enter an error message');
            return;
        }

        classifyMutation.mutate({
            error_message: errorInput,
            method: method,
            multi_search: multiSearch,
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

        // Determine which engine to teach based on classification method used
        let engine = method;
        if (method === 'MULTI_SEARCH') {
            // For multi-search, teach all engines
            // Start with the primary result's method if available
            engine = result?.method || 'VECTOR_DB';
        }

        teachMutation.mutate({
            error_text: errorInput,
            correct_doc_path: correctPath,
            engine: engine,
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
                    Enter an error message to find the relevant documentation
                </Typography>

                <Paper elevation={3} sx={{ p: 4, mb: 4 }}>
                    <SearchInput
                        errorInput={errorInput}
                        onErrorInputChange={setErrorInput}
                        method={method}
                        onMethodChange={setMethod}
                        multiSearch={multiSearch}
                        onMultiSearchChange={setMultiSearch}
                        onSearch={handleSearch}
                        isSearching={classifyMutation.isPending}
                    />
                </Paper>

                {/* Search Engines Comparison Section */}
                <Paper elevation={2} sx={{ p: 3, mb: 4, bgcolor: 'background.default' }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                        <Typography variant="h6" color="primary">
                            Search Engine Comparison
                        </Typography>
                        <Button
                            size="small"
                            onClick={() => setShowComparison(!showComparison)}
                            endIcon={<ExpandMoreIcon sx={{ transform: showComparison ? 'rotate(180deg)' : 'none', transition: '0.3s' }} />}
                        >
                            {showComparison ? 'Hide' : 'Show'} Details
                        </Button>
                    </Box>

                    {showComparison && comparisonData && (
                        <Box>
                            <Grid container spacing={2} sx={{ mb: 3 }}>
                                {comparisonData.engines.map((engine) => (
                                    <Grid item xs={12} md={4} key={engine.id}>
                                        <Card variant="outlined" sx={{ height: '100%' }}>
                                            <CardContent>
                                                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                                                    <Typography variant="h6" component="div" gutterBottom>
                                                        {engine.name}
                                                    </Typography>
                                                    <Chip
                                                        label={engine.available ? 'Available' : 'Unavailable'}
                                                        color={engine.available ? 'success' : 'default'}
                                                        size="small"
                                                    />
                                                </Box>
                                                
                                                <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 2 }}>
                                                    {engine.technology}
                                                </Typography>

                                                <Typography variant="body2" sx={{ mb: 2 }}>
                                                    {engine.description}
                                                </Typography>

                                                <Divider sx={{ my: 1.5 }} />

                                                <Typography variant="subtitle2" color="primary" gutterBottom>
                                                    Strengths:
                                                </Typography>
                                                <Box component="ul" sx={{ pl: 2, mt: 0.5, mb: 1.5 }}>
                                                    {engine.strengths.map((strength, idx) => (
                                                        <Typography component="li" variant="caption" key={idx} sx={{ mb: 0.5 }}>
                                                            {strength}
                                                        </Typography>
                                                    ))}
                                                </Box>

                                                <Typography variant="subtitle2" color="warning.main" gutterBottom>
                                                    Best For:
                                                </Typography>
                                                <Box component="ul" sx={{ pl: 2, mt: 0.5, mb: 0 }}>
                                                    {engine.best_for.map((use, idx) => (
                                                        <Typography component="li" variant="caption" key={idx} sx={{ mb: 0.5 }}>
                                                            {use}
                                                        </Typography>
                                                    ))}
                                                </Box>
                                            </CardContent>
                                        </Card>
                                    </Grid>
                                ))}
                            </Grid>

                            <Divider sx={{ my: 3 }} />

                            <Typography variant="h6" gutterBottom>
                                Feature Comparison Matrix
                            </Typography>
                            <Box sx={{ overflowX: 'auto' }}>
                                <Box component="table" sx={{ width: '100%', borderCollapse: 'collapse', mt: 2 }}>
                                    <Box component="thead">
                                        <Box component="tr">
                                            {comparisonData.comparison_matrix.headers.map((header, idx) => (
                                                <Box
                                                    component="th"
                                                    key={idx}
                                                    sx={{
                                                        textAlign: idx === 0 ? 'left' : 'center',
                                                        p: 1.5,
                                                        borderBottom: '2px solid',
                                                        borderColor: 'divider',
                                                        fontWeight: 'bold',
                                                        bgcolor: 'action.hover'
                                                    }}
                                                >
                                                    {header}
                                                </Box>
                                            ))}
                                        </Box>
                                    </Box>
                                    <Box component="tbody">
                                        {comparisonData.comparison_matrix.rows.map((row, rowIdx) => (
                                            <Box component="tr" key={rowIdx} sx={{ '&:hover': { bgcolor: 'action.hover' } }}>
                                                {row.map((cell, cellIdx) => (
                                                    <Box
                                                        component="td"
                                                        key={cellIdx}
                                                        sx={{
                                                            textAlign: cellIdx === 0 ? 'left' : 'center',
                                                            p: 1.5,
                                                            borderBottom: '1px solid',
                                                            borderColor: 'divider',
                                                            fontWeight: cellIdx === 0 ? 'medium' : 'normal'
                                                        }}
                                                    >
                                                        {cell}
                                                    </Box>
                                                ))}
                                            </Box>
                                        ))}
                                    </Box>
                                </Box>
                            </Box>

                            <Box sx={{ mt: 3, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
                                <Typography variant="subtitle2" color="info.dark" gutterBottom>
                                    Recommendations:
                                </Typography>
                                <Grid container spacing={1}>
                                    <Grid item xs={12} sm={6} md={4}>
                                        <Typography variant="caption" display="block">
                                            <strong>General Use:</strong> {comparisonData.recommendations.general_use}
                                        </Typography>
                                    </Grid>
                                    <Grid item xs={12} sm={6} md={4}>
                                        <Typography variant="caption" display="block">
                                            <strong>Production:</strong> {comparisonData.recommendations.production_deployment}
                                        </Typography>
                                    </Grid>
                                    <Grid item xs={12} sm={6} md={4}>
                                        <Typography variant="caption" display="block">
                                            <strong>Technical Queries:</strong> {comparisonData.recommendations.technical_queries}
                                        </Typography>
                                    </Grid>
                                </Grid>
                            </Box>
                        </Box>
                    )}
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
                                {result.multi_search && (
                                    <Chip
                                        label="Multi-Engine"
                                        color="success"
                                        size="small"
                                        sx={{ ml: 2 }}
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
                                        <strong>Consensus:</strong> {result.consensus_count} out of {result.total_methods} methods agree
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
                                        {result.multi_search ? 'Methods Used' : 'Method'}
                                    </Typography>
                                    <Chip 
                                        label={result.multi_search ? result.total_methods : method} 
                                        color="secondary" 
                                        sx={{ mt: 0.5 }} 
                                    />
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

                            {/* Multi-search individual results */}
                            {result.multi_search && result.all_results && result.all_results.length > 0 && (
                                <Box sx={{ mt: 3 }}>
                                    <Accordion>
                                        <AccordionSummary
                                            expandIcon={<ExpandMoreIcon />}
                                            aria-controls="individual-results-content"
                                            id="individual-results-header"
                                        >
                                            <Typography variant="body1" fontWeight="medium">
                                                Individual Method Results ({result.all_results.length})
                                            </Typography>
                                        </AccordionSummary>
                                        <AccordionDetails>
                                            <Grid container spacing={2}>
                                                {result.all_results.map((methodResult, idx) => (
                                                    <Grid item xs={12} key={idx}>
                                                        <Paper variant="outlined" sx={{ p: 2 }}>
                                                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                                                                <Chip label={methodResult.method} color="primary" size="small" />
                                                                <Chip 
                                                                    label={`${methodResult.confidence.toFixed(2)}%`} 
                                                                    color={getConfidenceColor(methodResult.confidence)}
                                                                    size="small"
                                                                />
                                                            </Box>
                                                            <Typography 
                                                                variant="body2" 
                                                                sx={{ 
                                                                    fontFamily: 'monospace', 
                                                                    fontSize: '0.85rem',
                                                                    bgcolor: 'grey.50',
                                                                    p: 1,
                                                                    borderRadius: 1
                                                                }}
                                                            >
                                                                {methodResult.doc_path}
                                                            </Typography>
                                                            {methodResult.is_fallback && (
                                                                <Typography variant="caption" color="warning.main" sx={{ mt: 0.5, display: 'block' }}>
                                                                    [WARNING] Fallback result
                                                                </Typography>
                                                            )}
                                                        </Paper>
                                                    </Grid>
                                                ))}
                                            </Grid>
                                        </AccordionDetails>
                                    </Accordion>
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
