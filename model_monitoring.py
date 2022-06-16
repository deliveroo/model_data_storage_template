import pandas as pd
import numpy as np
#regenerate identical synthetic data
np.random.seed(1234)
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pylab as plt
import ruptures as rpt



def drop_end_changepoints(change_points:pd.DataFrame,explode=True,keep_percentiles=[25,50,75])->pd.DataFrame:
    '''
    Drop artifical changepoints at end of timeseries
    
    INPUTS: change_points: pd.dataframe output of calculate_changepoints
    
    OUTPUTS: dfcp: pd.DataFrame output with end of file change points dropped
    '''
    df_cp = change_points.copy()
    df_cp1 = df_cp.set_index(['feature_name','datetime'])
    df_cp2 = df_cp.drop_duplicates(subset='feature_name',keep='last').set_index(['feature_name','datetime'])
    df_cp3 = df_cp1.drop(df_cp2.index).round(2).reset_index()
    if explode:
        df_cp3 = df_cp3.set_index(['feature_name','datetime']).apply(pd.Series.explode).reset_index()
        df_cp3 = df_cp3[df_cp3['percentile'].isin(keep_percentiles)]
    return df_cp3.reset_index(drop=True)




# Model Monitoring Utils
def generate_vlm_display(dfin:pd.DataFrame, pdf_file:str, 
                         percentiles:list = [25,50,75], 
                         percentile_lines:bool=False, 
                         change_points = None,
                         change_point_percentile_lines:bool=True):
    """
    Visualise the results of variable level monitoring. Creates a multi page pdf with vlm timeseries plots (one per page) and optiona change points overlaid.
    
    INPUTS:
    dfin: Input dataframe of timeseries features
    pdf_file: The output filename to save the multipage pdf
    percentiles: The percentiles to draw on the charts
    percentile_lines: bool. Do we show percentiles?
    change_points: None or pd.dataframe output of the change point analysis in the calculate_change_points function
    change_point_percentile_lines: bool. Do we show change point percentiles for each change point split?
    
    OUTPUT:
    None
    """
    df = dfin.copy()
    pdf_pages = PdfPages(pdf_file)
    nx,ny = np.shape(df)
    for i in range(ny):
        feature_name = df.columns[i]
        x = df.index
        y = df[feature_name].values
        
        # Create a figure instance (ie. a new page)
        fig = plt.figure(figsize=(8.27, 11.69), dpi=100)
        ax1 = fig.add_subplot(111)
        
        # Plot variable-level data
        y_percentiles = np.percentile(y, percentiles) 
        str_pc1 = ', '.join([str(int(pc))+'%' for pc in percentiles])+' percentiles'
        str_pc2 = ', '.join([str(np.round(pc,2)) for pc in y_percentiles])
        
        
           
        # add change points
        str_pc0 = '\n'
        if change_points is not None:
            change_points_dropna = change_points.dropna()
            cpnow = change_points_dropna[change_points_dropna['feature_name']==feature_name]
            ncp = len(cpnow)
            if ncp > 1:
                str_pc0 = str(int(ncp-1))+' change points detected\n'
            for i2 in range(ncp):
                datetime = cpnow['datetime'].iloc[i2]
                if ((ncp > 1) and (i2 < ncp-1)):
                    ax1.axvline(datetime,color='k',linewidth=2)
                if change_point_percentile_lines:
                    ypc = cpnow['value'].iloc[i2]
                    ax1.axhline(ypc[0],ls=':',color='k')
                    ax1.axhline(ypc[1],ls='--',color='k')
                    ax1.axhline(ypc[2],ls=':',color='k')
                    
        str_pc = str_pc0+ str_pc1+'\n'+str_pc2
        
        label = feature_name+': '+ str_pc            
        ax1.plot(x, y,label=label,zorder=0)
        ax1.set_ylabel('value')
        
        #show percentiles
        if percentile_lines:
            if change_points is not None:
                cpnow = change_points_dropna[change_points_dropna['feature_name']==feature_name]
                if len(cpnow) > 0:
                    continue
            ax1.axhline(y_percentiles[0],ls=':',color='k')
            ax1.axhline(y_percentiles[1],ls='--',color='k')
            ax1.axhline(y_percentiles[2],ls=':',color='k')
        
        
        # titles
        ax1.set_title(feature_name)
        ax1.legend()
        plt.grid()
    
        # Done with the page
        pdf_pages.savefig(fig)
        
    # save change point data to pdf
    if change_points is not None:
        df_cp3 = drop_end_changepoints(change_points_dropna)
        if len(df_cp3)>0:
            fig = plt.figure()
            fig.suptitle('VLM Change Point Summary')
            table = plt.table(cellText=df_cp3.values, colLabels=df_cp3.columns, loc='center',
                  colWidths=[0.1 for col in range(df_cp3.columns.size)])
            table.auto_set_font_size(True)
            #table.set_fontsize(24)
            #table.scale(2, 2)
            plt.axis('off')
            pdf_pages.savefig()
    

    pdf_pages.close()


def calculate_change_points(dfin:pd.DataFrame, 
                            percentiles:list= [25,50,75], 
                            explode:bool=True,
                            keep_last_changepoint=True,
                            trend_penalty:int = 10, 
                            rolling_sd_window:int = 10, 
                            rolling_sd_penalty:int=10)->pd.DataFrame:
    """
    Calculate change points in a dataframe of timeseries data
    INPUTS:
    dfin: Input pandas dataframe
    percentiles: Percentiles to report levels
    explode = boolean explode the percentiles in the output dataframe or keep as list form
    keep_last_changepoint = False, bbyu default changepoint analysis keeps the last point in the timeseries regardless of any changepoints. Useful for plotting in the generate_vlm_display function but less useful for clarity
    trend_penalty = 10 default ruptures change point sensitivity parameter, lower means more change points identified but introduces noise
    rolling_sd_window: set to None else sets the window for standard deviation anomaly detection to identify timeseries whose levels may not change but with periods of variable volatility
    rolling_sd_penalty: as with trend_penalty but for the rolling sd anomaly detection
    
    OUTPUT:
    df_cp: pandas dataframe of change points
    
    """
    df = dfin.copy()
    nx,ny = np.shape(df)
    df_cp = pd.DataFrame({})
    for i in range(ny):
        
        feature_name = df.columns[i]
        x = df.index
        y = df[feature_name].values
        
        
        
        #identify nans
        idx_nan = np.where(y!=y)[0]
        x_nan = list(x[idx_nan])
        dfn = pd.DataFrame({'feature_name':[feature_name]*len(x_nan),'datetime':x_nan,'percentile':[np.nan]*len(x_nan),'value':[np.nan]*len(x_nan),'description':['NaN']*len(x_nan)})
        df_cp = pd.concat([df_cp, dfn])
        
        
        #indentify infs
        idx_inf = np.where(np.isinf(y))[0]
        x_inf = list(x[idx_inf])
        dfn = pd.DataFrame({'feature_name':[feature_name]*len(x_inf),'datetime':x_inf,'percentile':[np.nan]*len(x_nan),'value':[np.nan]*len(x_inf),'description':['Inf']*len(x_inf)})
        df_cp = pd.concat([df_cp, dfn])
        
        #remove these for trend bit
        ys = pd.Series(y)
        ys.iloc[idx_inf]=np.nan
        y = ys.fillna(method='ffill').values
        
        algo = rpt.Pelt(model="rbf").fit(y)
        result = algo.predict(pen=10)
        
        
        #apply rolling standard deviation filter
        if rolling_sd_window is not None:
            yrsd = pd.Series(y).rolling(rolling_sd_window).std().shift(-int(rolling_sd_window/2)).dropna()
            algo = rpt.Pelt(model="rbf").fit(y)
            ap = algo.predict(pen=10)
            result = result + ap
            result = list(set(result))
            result.sort()
        
        
        
        idxlo = 0
        for r in result:
            yn = y[idxlo:r]
            y_pc = np.percentile(yn,percentiles)
            idxlo = r
            dfn = pd.DataFrame({'feature_name':[feature_name],'datetime':[x[min(nx-1,r)]],'percentile':[percentiles],'value':[y_pc],'description':['trend/volatility']})
            df_cp = pd.concat([df_cp, dfn])
        
        
        
            
    
    df_cp['datetime']=pd.to_datetime(df_cp['datetime']).dt.date
    
    if keep_last_changepoint is False:
        df_cp = drop_end_changepoints(df_cp)
    
    if explode:
        df_cp = df_cp.set_index(['feature_name','datetime']).apply(pd.Series.explode).reset_index()
        
    
    
    return df_cp.reset_index(drop=True)
    
    
    
if __name__ == '__main__':

    # Ingest model input features data pull (previous-1yr)
    #
    #
    #
    ## this is just a template so create some synthetic data here
    n_features = 7
    n_history = 365
    end_date = pd.Timestamp.today().date()
    start_date = end_date - pd.Timedelta(str(int(n_history-1))+'D')
    dates = pd.date_range(start_date, end_date, freq='1d')
    X = np.random.randn(n_history,n_features)
    ## inject artificial feature offsets
    offsets = 5*np.random.randn(n_features)
    X = X + offsets
    ## inject artifical trend
    idx_trend_feature = 4
    idx_trend_start = int(n_history/2)
    idx_trend_end = int(3/4*n_history)
    trend = 0.1*(np.arange(n_history) - idx_trend_start) + X[idx_trend_start,idx_trend_feature]
    trend[:idx_trend_start]=0
    trend[idx_trend_end:]=trend[idx_trend_end]
    X[:, idx_trend_feature] += trend 
    
    
    #Add nans and infinities
    X[10:12,3]=np.nan
    X[40:42,3] = np.inf
    
    
    ## simulate dead-period
    idx_trend_feature = 5
    idx_trend_start = int(n_history/2)
    idx_trend_end = int(3/4*n_history)
    X[idx_trend_start:idx_trend_end, idx_trend_feature] = 0
    
    ## volatility change
    idx_trend_feature = 6
    idx_trend_start = int(n_history/2)
    idx_trend_end = int(3/4*n_history)
    xm = X[idx_trend_start:idx_trend_end, idx_trend_feature].mean()
    X[idx_trend_start:idx_trend_end, idx_trend_feature] = (X[idx_trend_start:idx_trend_end, idx_trend_feature] - xm)*10 + xm
    
    
    # create feature dataframe 
    df = pd.DataFrame(X,columns = ['feature_'+str(i) for i in range(n_features)])
    df.index = dates
    
    
    ## Change-point detection
    change_points_for_chart = calculate_change_points(df, percentiles= [25,50,75],explode=False)
    change_points = drop_end_changepoints(change_points_for_chart,explode=False)
    
    ## Monitoring Output
    pdf_file = './img/variable_level_monitoring.pdf'
    generate_vlm_display(df, pdf_file, percentiles = [25,50,75], change_points=change_points_for_chart)
    
    
    
    
    
    
    