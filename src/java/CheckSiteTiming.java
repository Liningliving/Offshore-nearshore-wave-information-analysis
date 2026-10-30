import java.io.*;
import java.nio.file.*;
import java.time.*;
import java.util.*;
import infodynamics.measures.continuous.kraskov.*;

/** Load a site's cleaned file, verify Java metadata; do not calculate main-data MI/CMI. */
public class CheckSiteTiming {
  public static void main(String[] args)throws Exception {
    List<String> lines=Files.readAllLines(Path.of(args[0]));String[] header=lines.get(0).split(",");Map<String,Integer> cols=new HashMap<>();for(int i=0;i<header.length;i++)cols.put(header[i],i);
    int n=lines.size()-1;int[] hours=new int[n];double[][] ho=new double[n][1],hn=new double[n][1],tp=new double[n][1],dir=new double[n][2];long first=0;
    for(int i=0;i<n;i++){
      String[] f=lines.get(i+1).split(",");long t=OffsetDateTime.parse(f[cols.get("timestamp_utc")].replace(' ','T')).toEpochSecond();
      if(i==0)first=t;if((t-first)%3600!=0||t%3600!=0)throw new IllegalArgumentException("Off-grid time");hours[i]=Math.toIntExact((t-first)/3600);
      ho[i][0]=Double.parseDouble(f[cols.get("Ho")]);hn[i][0]=Double.parseDouble(f[cols.get("Hn")]);tp[i][0]=Double.parseDouble(f[cols.get("Tp_o")]);dir[i][0]=Double.parseDouble(f[cols.get("Dx")]);dir[i][1]=Double.parseDouble(f[cols.get("Dy")]);
    }
    MutualInfoCalculatorMultiVariateKraskov1 mi=new MutualInfoCalculatorMultiVariateKraskov1();mi.setProperty("NOISE_LEVEL_TO_ADD","0");ElapsedHourLoader.load(mi,hours,ho,hn,4,45);
    ConditionalMutualInfoCalculatorMultiVariateKraskov1 period=new ConditionalMutualInfoCalculatorMultiVariateKraskov1();period.setProperty("NOISE_LEVEL_TO_ADD","0");ElapsedHourLoader.load(period,hours,tp,hn,ho,4,45);
    ConditionalMutualInfoCalculatorMultiVariateKraskov1 direction=new ConditionalMutualInfoCalculatorMultiVariateKraskov1();direction.setProperty("NOISE_LEVEL_TO_ADD","0");ElapsedHourLoader.load(direction,hours,dir,hn,ho,4,45);
    int runs=1;for(int i=1;i<n;i++)if(hours[i]-hours[i-1]!=1)runs++;
    System.out.println("{\"observations\":"+n+",\"segments\":"+runs+",\"all_time_indices_and_set_ids_verified\":true,\"mi_observations\":"+mi.getNumObservations()+",\"period_cmi_observations\":"+period.getNumObservations()+",\"direction_cmi_observations\":"+direction.getNumObservations()+",\"main_information_estimates_computed\":false}");
  }
}
