import React, { useState } from 'react';
import {
    Paper,
    Box,
    Typography,
    Button,
    Card,
    CardContent,
    Divider,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

function EngineInfoSection({ comparisonData }) {
    const [showDetails, setShowDetails] = useState(false);

    if (!comparisonData?.engines?.[0]) {
        return null;
    }

    const engine = comparisonData.engines[0];

    return (
        <Paper elevation={2} sx={{ p: 3, mb: 4, bgcolor: 'background.default' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" color="primary">
                    About Hybrid Custom Search
                </Typography>
                <Button
                    size="small"
                    onClick={() => setShowDetails(!showDetails)}
                    endIcon={
                        <ExpandMoreIcon
                            sx={{ transform: showDetails ? 'rotate(180deg)' : 'none', transition: '0.3s' }}
                        />
                    }
                >
                    {showDetails ? 'Hide' : 'Show'} Details
                </Button>
            </Box>

            {showDetails && (
                <Box>
                    <Card variant="outlined">
                        <CardContent>
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
                </Box>
            )}
        </Paper>
    );
}

export default EngineInfoSection;
