import React from 'react';
import {
    Box,
    Accordion,
    AccordionSummary,
    AccordionDetails,
    Typography,
    CircularProgress,
    Paper,
    Alert,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import DescriptionIcon from '@mui/icons-material/Description';

function DocumentationPreview({ docContent, isLoading }) {
    return (
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
                    {isLoading ? (
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
                        <Alert severity="warning">Unable to load documentation content</Alert>
                    )}
                </AccordionDetails>
            </Accordion>
        </Box>
    );
}

export default DocumentationPreview;
