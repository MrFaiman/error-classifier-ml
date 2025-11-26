import React from 'react';
import {
    Box,
    Button,
    CircularProgress,
    FormControl,
    FormControlLabel,
    Grid,
    InputLabel,
    MenuItem,
    Select,
    Switch,
    TextField,
    Typography,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';

function SearchInput({
    errorInput,
    onErrorInputChange,
    method,
    onMethodChange,
    multiSearch,
    onMultiSearchChange,
    onSearch,
    isSearching,
}) {
    return (
        <Grid container spacing={3}>
            <Grid item xs={12} sm={8}>
                <FormControl fullWidth disabled={multiSearch}>
                    <InputLabel>Classification Method</InputLabel>
                    <Select
                        value={method}
                        label="Classification Method"
                        onChange={(e) => onMethodChange(e.target.value)}
                    >
                        <MenuItem value="CUSTOM_TFIDF">Custom TF-IDF (No Blackbox)</MenuItem>
                        <MenuItem value="ENHANCED_CUSTOM">Enhanced Custom (All ML Algorithms)</MenuItem>
                        <MenuItem value="HYBRID_CUSTOM">Hybrid Custom (TF-IDF + BM25)</MenuItem>
                    </Select>
                </FormControl>
            </Grid>

            <Grid item xs={12} sm={4}>
                <FormControlLabel
                    control={
                        <Switch
                            checked={multiSearch}
                            onChange={(e) => onMultiSearchChange(e.target.checked)}
                            color="primary"
                        />
                    }
                    label={
                        <Box>
                            <Typography variant="body2" fontWeight="medium">
                                Multi-Engine Search
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                                Aggregate all methods
                            </Typography>
                        </Box>
                    }
                />
            </Grid>

            <Grid item xs={12}>
                <TextField
                    fullWidth
                    multiline
                    rows={4}
                    label="Error Message"
                    placeholder="Enter the error message or log snippet..."
                    value={errorInput}
                    onChange={(e) => onErrorInputChange(e.target.value)}
                    variant="outlined"
                />
            </Grid>

            <Grid item xs={12}>
                <Button
                    fullWidth
                    variant="contained"
                    size="large"
                    startIcon={isSearching ? <CircularProgress size={20} color="inherit" /> : <SearchIcon />}
                    onClick={onSearch}
                    disabled={isSearching || !errorInput.trim()}
                >
                    {isSearching ? 'Classifying...' : 'Classify Error'}
                </Button>
            </Grid>
        </Grid>
    );
}

export default SearchInput;
