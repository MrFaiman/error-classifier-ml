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
import { useForm } from '@tanstack/react-form';
import { classifyError, teachCorrection, getDocContent, getSearchEnginesComparison } from '../services/api';
import SearchInput from '../components/SearchInput';

function SearchPage() {
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);
    const [feedbackGiven, setFeedbackGiven] = useState(null);
    const [openCorrectionDialog, setOpenCorrectionDialog] = useState(false);
    const [feedbackSuccess, setFeedbackSuccess] = useState(null);
    const [showComparison, setShowComparison] = useState(false);
    const [currentErrorMessage, setCurrentErrorMessage] = useState('');

    // TanStack Form for correction dialog
    const correctionForm = useForm({
        defaultValues: {
            correctPath: '',
        },
        onSubmit: async ({ value }) => {
            teachMutation.mutate({
                error_text: currentErrorMessage,
                correct_doc_path: value.correctPath,
                engine: 'HYBRID_CUSTOM',
            });
        },
    });

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
            correctionForm.reset();
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

    const handleSearch = (errorMessage) => {
        setCurrentErrorMessage(errorMessage);
        classifyMutation.mutate({
            error_message: errorMessage,
            method: 'HYBRID_CUSTOM',
            multi_search: false,
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

    const handleCloseCorrectionDialog = () => {
        setOpenCorrectionDialog(false);
        correctionForm.reset();
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
                    Error Classification
                </Typography>
                <Typography variant="body1" color="text.secondary" align="center" sx={{ mb: 4 }}>
                    Enter an error message to find the relevant documentation using Hybrid Search (TF-IDF + BM25)
                </Typography>

                <Paper elevation={3} sx={{ p: 4, mb: 4 }}>
                    <SearchInput
                        onSubmit={handleSearch}
                        isSearching={classifyMutation.isPending}
                    />
                </Paper>

                {/* Search Engine Info Section */}
                <Paper elevation={2} sx={{ p: 3, mb: 4, bgcolor: 'background.default' }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                        <Typography variant="h6" color="primary">
                            About Hybrid Custom Search
                        </Typography>
                        <Button
                            size="small"
                            onClick={() => setShowComparison(!showComparison)}
                            endIcon={<ExpandMoreIcon sx={{ transform: showComparison ? 'rotate(180deg)' : 'none', transition: '0.3s' }} />}
                        >
                            {showComparison ? 'Hide' : 'Show'} Details
                        </Button>
                    </Box>

                    {showComparison && comparisonData?.engines && comparisonData.engines[0] && (
                        <Box>
                            <Card variant="outlined">
                                <CardContent>
                                    <Typography variant="body2" sx={{ mb: 2 }}>
                                        {comparisonData.engines[0].description}
                                    </Typography>

                                    <Divider sx={{ my: 1.5 }} />

                                    <Typography variant="subtitle2" color="primary" gutterBottom>
                                        Strengths:
                                    </Typography>
                                    <Box component="ul" sx={{ pl: 2, mt: 0.5, mb: 1.5 }}>
                                        {comparisonData.engines[0].strengths.map((strength, idx) => (
                                            <Typography component="li" variant="caption" key={idx} sx={{ mb: 0.5 }}>
                                                {strength}
                                            </Typography>
                                        ))}
                                    </Box>

                                    <Typography variant="subtitle2" color="warning.main" gutterBottom>
                                        Best For:
                                    </Typography>
                                    <Box component="ul" sx={{ pl: 2, mt: 0.5, mb: 0 }}>
                                        {comparisonData.engines[0].best_for.map((use, idx) => (
                                            <Typography component="li" variant="caption" key={idx} sx={{ mb: 0.5 }}>
                                                {use}
                                            </Typography>
                                        ))}
                                    </Box>
                                </CardContent>
                            </Card>

                            <Box sx={{ mt: 2, p: 2, bgcolor: 'success.light', borderRadius: 1 }}>
                                <Typography variant="body2" color="success.dark" fontWeight="medium">
                                    ✅ 100% custom implementation - no blackbox libraries!
                                </Typography>
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
                        <form
                            onSubmit={(e) => {
                                e.preventDefault();
                                e.stopPropagation();
                                correctionForm.handleSubmit();
                            }}
                            id="correction-form"
                        >
                            <Box sx={{ mt: 2 }}>
                                <Typography variant="body2" color="text.secondary" gutterBottom>
                                    Help us improve! Please enter the correct documentation path for this error.
                                </Typography>
                                <correctionForm.Field
                                    name="correctPath"
                                    validators={{
                                        onChange: ({ value }) =>
                                            !value || value.trim().length === 0
                                                ? 'Please enter the correct documentation path'
                                                : undefined,
                                    }}
                                >
                                    {(field) => (
                                        <TextField
                                            fullWidth
                                            label="Correct Documentation Path"
                                            placeholder="e.g., dataset/docs/services/logitrack/SECURITY_ALERT.md"
                                            value={field.state.value}
                                            onChange={(e) => field.handleChange(e.target.value)}
                                            onBlur={field.handleBlur}
                                            error={field.state.meta.errors.length > 0}
                                            helperText={
                                                field.state.meta.errors[0] ||
                                                'The system will learn from your correction'
                                            }
                                            sx={{ mt: 2 }}
                                        />
                                    )}
                                </correctionForm.Field>
                            </Box>
                        </form>
                    </DialogContent>
                    <DialogActions>
                        <Button onClick={handleCloseCorrectionDialog}>Cancel</Button>
                        <Button
                            type="submit"
                            form="correction-form"
                            variant="contained"
                            color="primary"
                            disabled={teachMutation.isPending}
                        >
                            {teachMutation.isPending ? 'Submitting...' : 'Submit Correction'}
                        </Button>
                    </DialogActions>
                </Dialog>
            </Box>
        </Container>
    );
}

export default SearchPage;
