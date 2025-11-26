import React from 'react';
import {
    Box,
    Accordion,
    AccordionSummary,
    AccordionDetails,
    Typography,
    Grid,
    Paper,
    Chip,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import LightbulbIcon from '@mui/icons-material/Lightbulb';

function MultiSearchResults({ results, getConfidenceColor }) {
    if (!results || results.length === 0) {
        return null;
    }

    return (
        <Box sx={{ mt: 3 }}>
            <Accordion>
                <AccordionSummary
                    expandIcon={<ExpandMoreIcon />}
                    aria-controls="individual-results-content"
                    id="individual-results-header"
                >
                    <Typography variant="body1" fontWeight="medium">
                        Individual Method Results ({results.length})
                    </Typography>
                </AccordionSummary>
                <AccordionDetails>
                    <Grid container spacing={2}>
                        {results.map((methodResult, idx) => (
                            <Grid item xs={12} key={idx}>
                                <Paper variant="outlined" sx={{ p: 2 }}>
                                    <Box
                                        sx={{
                                            display: 'flex',
                                            justifyContent: 'space-between',
                                            alignItems: 'center',
                                            mb: 1,
                                        }}
                                    >
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
                                            borderRadius: 1,
                                        }}
                                    >
                                        {methodResult.doc_path}
                                    </Typography>
                                    {methodResult.explanation && (
                                        <Box sx={{ mt: 2 }}>
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
                                                <LightbulbIcon fontSize="small" color="primary" />
                                                <Typography variant="caption" color="text.secondary" fontWeight="medium">
                                                    Explanation
                                                </Typography>
                                            </Box>
                                            <Typography
                                                variant="body2"
                                                sx={{
                                                    fontSize: '0.85rem',
                                                    bgcolor: 'primary.50',
                                                    p: 1.5,
                                                    borderRadius: 1,
                                                    lineHeight: 1.6,
                                                    border: '1px solid',
                                                    borderColor: 'primary.100'
                                                }}
                                            >
                                                {methodResult.explanation}
                                            </Typography>
                                        </Box>
                                    )}
                                    {methodResult.is_fallback && (
                                        <Typography
                                            variant="caption"
                                            color="warning.main"
                                            sx={{ mt: 0.5, display: 'block' }}
                                        >
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
    );
}

export default MultiSearchResults;
