import React, { useState } from 'react';
import { Container, Paper, Box, Typography, Alert } from '@mui/material';
import { useMutation, useQuery } from '@tanstack/react-query';
import { classifyError, teachCorrection, getDocContent, getSearchEnginesComparison } from '../services/api';
import SearchInput from '../components/SearchInput';
import EngineInfoSection from '../components/EngineInfoSection';
import ClassificationResult from '../components/ClassificationResult';
import DocumentationPreview from '../components/DocumentationPreview';
import MultiSearchResults from '../components/MultiSearchResults';
import CorrectionDialog from '../components/CorrectionDialog';

function SearchPage() {
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);
    const [feedbackGiven, setFeedbackGiven] = useState(null);
    const [openCorrectionDialog, setOpenCorrectionDialog] = useState(false);
    const [feedbackSuccess, setFeedbackSuccess] = useState(null);
    const [currentErrorMessage, setCurrentErrorMessage] = useState('');

    // Query for search engines comparison
    const { data: comparisonData } = useQuery({
        queryKey: ['searchEnginesComparison'],
        queryFn: getSearchEnginesComparison,
        staleTime: Infinity,
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
        setFeedbackGiven(null);
    };

    const handleSubmitCorrection = (correctPath) => {
        teachMutation.mutate({
            error_text: currentErrorMessage,
            correct_doc_path: correctPath,
            engine: 'HYBRID_CUSTOM',
        });
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

                <EngineInfoSection comparisonData={comparisonData} />

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
                    <Box>
                        <ClassificationResult
                            result={result}
                            feedbackGiven={feedbackGiven}
                            onPositiveFeedback={handlePositiveFeedback}
                            onNegativeFeedback={handleNegativeFeedback}
                            onCopyPath={handleCopyPath}
                            getConfidenceColor={getConfidenceColor}
                        />

                        {result.multi_search && result.all_results && result.all_results.length > 0 && (
                            <MultiSearchResults
                                results={result.all_results}
                                getConfidenceColor={getConfidenceColor}
                            />
                        )}

                        <DocumentationPreview docContent={docContent} isLoading={isLoadingDoc} />
                    </Box>
                )}

                <CorrectionDialog
                    open={openCorrectionDialog}
                    onClose={handleCloseCorrectionDialog}
                    onSubmit={handleSubmitCorrection}
                    isPending={teachMutation.isPending}
                />
            </Box>
        </Container>
    );
}

export default SearchPage;
